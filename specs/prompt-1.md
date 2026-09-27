Build a React + Vite frontend with a Python FastAPI backend for Zerodha Kite Connect login.

Create a login page with:

API Key
API Secret
Request Token
Login button
On Login, send the values to FastAPI, use the Kite Connect SDK to generate the access token, save the token on the backend, and never show it in the browser.

Reuse the saved access token during local development so the user does not need to log in again after every code change.

Then navigate to a dashboard.

The dashboard should have tabs.

Create a User tab that calls the backend profile API and displays:

User Name
User ID
Products
Exchanges
Use a clean dashboard design and create it in dark mode, while keeping the UI easy to customize.

Keep the UI professional, beginner-friendly, and include setup/run instructions.