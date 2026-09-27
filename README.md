# ALGO TRADING

## ZERODHA KITE CONNECT SDK for python (Broker API)

Your Kite login URL is:

[Open Kite Connect login](https://kite.zerodha.com/connect/login?v=3&api_key=)

## Kite Desk

A local React + Vite dashboard backed by FastAPI and the official Kite Connect Python SDK. The access token is stored in `backend/.data/token.json` on this machine and is never returned to the browser. The API secret is used only during login and is not saved.

### Requirements

- Python 3.10 or newer
- Node.js 18 or newer (includes npm)
- An active Zerodha account and Kite Connect app with its API key and API secret

### Start the backend (Windows PowerShell)

Open a terminal in the repository and run:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal open. The API listens only on your local machine. Interactive API documentation is available at [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs).

### Start the frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### Log in

1. In the Kite Connect developer console, configure the app's redirect URL to the callback URL used by your Kite app.
2. Open the Kite Connect login URL for your API key. Replace the empty `api_key` value in the login link at the top of this README with your key.
3. Sign in to Zerodha. Kite redirects to your configured callback URL with a short-lived `request_token` query parameter. Copy its value.
4. Enter your API key, API secret, and request token in Kite Desk, then choose **Connect to Kite**.

On successful login, the backend exchanges the request token, validates the profile, and saves the access token locally. Reloading or restarting the development servers reuses that saved session while Kite considers it valid. If Kite expires or revokes it, sign in again with a fresh request token. **Never share or commit `backend/.data/token.json`; it contains an active credential.** The file is excluded by `.gitignore`.

### Local customization

- Edit the color, spacing, and typography variables near the top of `frontend/src/styles.css`.
- The Vite development server proxies `/api` to `http://127.0.0.1:8000`; adjust `frontend/vite.config.js` if you change the backend port.
- Set `FRONTEND_ORIGIN` to change the allowed browser origin, or `KITE_TOKEN_FILE` to store the session file at a different local path.

This app is intended for local development, not public deployment. Keep the backend bound to `127.0.0.1` and do not expose the token file or API to the internet.
