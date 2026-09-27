import json
import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kiteconnect import KiteConnect
from kiteconnect.exceptions import KiteException
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = Path(os.getenv("KITE_TOKEN_FILE", BASE_DIR / ".data" / "token.json"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

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


@app.post("/api/logout")
def logout() -> dict[str, bool]:
    TOKEN_FILE.unlink(missing_ok=True)
    return {"authenticated": False}