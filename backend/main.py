import csv
import io
import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kiteconnect import KiteConnect
from kiteconnect.exceptions import KiteException
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = Path(os.getenv("KITE_TOKEN_FILE", BASE_DIR / ".data" / "token.json"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
NIFTY_100_CSV_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"

app = FastAPI(title="Kite Local API", docs_url="/api/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class LoginRequest(BaseModel):
    api_key: str = Field(min_length=1, max_length=128)
    api_secret: str = Field(min_length=1, max_length=256)
    request_token: str = Field(min_length=1, max_length=256)


class SignalsRequest(BaseModel):
    short_sma: int = Field(default=6, ge=1, le=100)
    long_sma: int = Field(default=30, ge=2, le=200)
    lookback_days: int = Field(default=90, ge=1, le=1000)
    max_stocks: int = Field(default=25, ge=1, le=100)


def read_session() -> dict[str, str] | None:
    try:
        data: Any = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    api_key = data.get("api_key")
    access_token = data.get("access_token")
    if not isinstance(api_key, str) or not isinstance(access_token, str):
        return None
    return {"api_key": api_key, "access_token": access_token}


def save_session(api_key: str, access_token: str) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=TOKEN_FILE.parent, delete=False
        ) as temporary_file:
            json.dump({"api_key": api_key, "access_token": access_token}, temporary_file)
            temporary_path = Path(temporary_file.name)
        temporary_path.replace(TOKEN_FILE)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def kite_for_session(session: dict[str, str]) -> KiteConnect:
    kite = KiteConnect(api_key=session["api_key"])
    kite.set_access_token(session["access_token"])
    return kite


def safe_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_name": profile.get("user_name", ""),
        "user_id": profile.get("user_id", ""),
        "products": profile.get("products", []),
        "exchanges": profile.get("exchanges", []),
    }


def fetch_nifty_100_constituents() -> list[dict[str, str]]:
    request = Request(
        NIFTY_100_CSV_URL,
        headers={"User-Agent": "Mozilla/5.0 KiteDesk/1.0"},
    )
    with urlopen(request, timeout=20) as response:
        content = response.read().decode("utf-8-sig")
    constituents = []
    for row in csv.DictReader(io.StringIO(content)):
        symbol = (row.get("Symbol") or "").strip()
        company = (row.get("Company Name") or "").strip()
        if symbol:
            constituents.append({"symbol": symbol, "company": company})
    if not constituents:
        raise ValueError("The Nifty 100 constituent list was empty or had an unexpected format.")
    return constituents


def latest_crossover(
    candles: list[dict[str, Any]], short_period: int, long_period: int, lookback_days: int
) -> dict[str, Any] | None:
    closes = [float(candle["close"]) for candle in candles]
    if len(closes) < long_period + 1:
        return None

    latest_index = len(closes) - 1
    first_index = max(long_period, latest_index - lookback_days + 1)
    for index in range(latest_index, first_index - 1, -1):
        short_now = sum(closes[index - short_period + 1 : index + 1]) / short_period
        long_now = sum(closes[index - long_period + 1 : index + 1]) / long_period
        short_before = sum(closes[index - short_period : index]) / short_period
        long_before = sum(closes[index - long_period : index]) / long_period
        if short_before <= long_before and short_now > long_now:
            crossover_type = "Bullish"
        elif short_before >= long_before and short_now < long_now:
            crossover_type = "Bearish"
        else:
            continue
        return {
            "crossover_type": crossover_type,
            "crossover_date": candles[index]["date"].date().isoformat(),
            "close": closes[index],
            "short_sma": short_now,
            "long_sma": long_now,
        }
    return None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/session")
def session_status() -> dict[str, bool]:
    session = read_session()
    if session is None:
        return {"authenticated": False}
    try:
        kite_for_session(session).profile()
    except KiteException:
        return {"authenticated": False}
    return {"authenticated": True}


@app.post("/api/login")
def login(payload: LoginRequest) -> dict[str, bool]:
    kite = KiteConnect(api_key=payload.api_key)
    try:
        session_data = kite.generate_session(
            payload.request_token, api_secret=payload.api_secret
        )
        access_token = session_data["access_token"]
        kite.set_access_token(access_token)
        kite.profile()
    except (KiteException, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=401,
            detail="Kite rejected the login details or request token. Generate a fresh request token and try again.",
        ) from error
    save_session(payload.api_key, access_token)
    return {"authenticated": True}


@app.get("/api/profile")
def profile() -> dict[str, Any]:
    session = read_session()
    if session is None:
        raise HTTPException(status_code=401, detail="Log in to Kite Connect first.")
    try:
        return safe_profile(kite_for_session(session).profile())
    except KiteException as error:
        raise HTTPException(
            status_code=401,
            detail="The saved Kite session has expired. Log in again.",
        ) from error


@app.post("/api/signals")
def signals(payload: SignalsRequest) -> dict[str, Any]:
    if payload.short_sma >= payload.long_sma:
        raise HTTPException(status_code=422, detail="Short SMA must be smaller than Long SMA.")
    session = read_session()
    if session is None:
        raise HTTPException(status_code=401, detail="Log in to Kite Connect first.")

    try:
        constituents = fetch_nifty_100_constituents()
    except (OSError, URLError, UnicodeDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="Could not load the official Nifty 100 constituent list. Try again shortly.",
        ) from error

    kite = kite_for_session(session)
    try:
        instruments = kite.instruments("NSE")
    except KiteException as error:
        raise HTTPException(status_code=502, detail="Kite could not load NSE instruments.") from error

    token_by_symbol = {
        instrument["tradingsymbol"]: instrument["instrument_token"]
        for instrument in instruments
        if instrument.get("tradingsymbol") and instrument.get("instrument_token")
    }
    start_date = date.today() - timedelta(days=(payload.long_sma + payload.lookback_days) * 2 + 14)
    end_date = date.today()
    results = []
    matched_count = 0
    for constituent in constituents:
        symbol = constituent["symbol"]
        instrument_token = token_by_symbol.get(symbol)
        if instrument_token is None:
            continue
        matched_count += 1
        try:
            candles = kite.historical_data(
                instrument_token,
                start_date,
                end_date,
                "day",
                continuous=False,
                oi=False,
            )
        except KiteException:
            continue
        crossover = latest_crossover(
            candles, payload.short_sma, payload.long_sma, payload.lookback_days
        )
        if crossover is not None:
            results.append({
                "ticker": symbol,
                "company": constituent["company"],
                **crossover,
            })

    results.sort(key=lambda result: result["crossover_date"], reverse=True)
    return {
        "signals": results[: payload.max_stocks],
        "scanned_symbols": len(constituents),
        "matched_symbols": matched_count,
        "short_sma": payload.short_sma,
        "long_sma": payload.long_sma,
        "lookback_days": payload.lookback_days,
    }


@app.post("/api/logout")
def logout() -> dict[str, bool]:
    TOKEN_FILE.unlink(missing_ok=True)
    return {"authenticated": False}