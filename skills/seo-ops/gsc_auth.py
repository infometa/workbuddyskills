#!/usr/bin/env python3
"""
Google Search Console OAuth Setup

One-time authentication flow for GSC API access.
Opens a browser for Google Sign-In, exchanges the auth code for a token,
and saves the token locally for use by gsc_client.py.

Prerequisites:
    1. Create a Google Cloud project with Search Console API enabled
    2. Create OAuth 2.0 credentials (Desktop application type)
    3. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars
       OR set GOOGLE_CREDENTIALS_FILE to a JSON file with client_id/client_secret

Usage:
    python gsc_auth.py
"""

import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

# Configuration
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("GSC_REDIRECT_URI", "http://localhost:8765")
SCOPES = "https://www.googleapis.com/auth/webmasters.readonly"
TOKEN_FILE = os.environ.get("GSC_TOKEN_FILE", os.path.join(os.path.dirname(__file__), ".gsc-token.json"))

# Try loading from credentials file if env vars not set
CREDS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "")
if CREDS_FILE and os.path.exists(CREDS_FILE) and (not CLIENT_ID or not CLIENT_SECRET):
    with open(CREDS_FILE) as f:
        creds = json.load(f)
    CLIENT_ID = CLIENT_ID or creds.get("client_id", "")
    CLIENT_SECRET = CLIENT_SECRET or creds.get("client_secret", "")

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: Google OAuth credentials required.")
    print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables,")
    print("or set GOOGLE_CREDENTIALS_FILE to a JSON file with client_id/client_secret.")
    print("\nTo create credentials:")
    print("  1. Go to https://console.cloud.google.com/apis/credentials")
    print("  2. Create OAuth 2.0 Client ID (Desktop application)")
    print("  3. Download the JSON and set GOOGLE_CREDENTIALS_FILE, or copy the values")
    exit(1)

auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = parse_qs(urlparse(self.path).query)
        auth_code = query.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>GSC Authorized! You can close this tab.</h1>")
    def log_message(self, *args):
        pass

# Build auth URL
auth_url = (
    f"https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={CLIENT_ID}&"
    f"redirect_uri={REDIRECT_URI}&"
    f"response_type=code&"
    f"scope={SCOPES}&"
    f"access_type=offline&"
    f"prompt=consent"
)

print("Opening browser for Google Sign-In...")
print(f"If the browser doesn't open, visit:\n{auth_url}\n")
webbrowser.open(auth_url)

# Wait for callback
port = int(REDIRECT_URI.split(":")[-1])
server = HTTPServer(("localhost", port), CallbackHandler)
server.handle_request()

if not auth_code:
    print("ERROR: No auth code received")
    exit(1)

# Exchange code for token
print("Exchanging code for token...")
resp = requests.post("https://oauth2.googleapis.com/token", data={
    "code": auth_code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code"
})

if resp.status_code != 200:
    print(f"ERROR: Token exchange failed — {resp.text}")
    exit(1)

token_data = resp.json()
with open(TOKEN_FILE, "w") as f:
    json.dump(token_data, f, indent=2)
os.chmod(TOKEN_FILE, 0o600)

print(f"✅ GSC token saved to {TOKEN_FILE}")

# Quick verification
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    cred = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )
    service = build("searchconsole", "v1", credentials=cred)
    sites = service.sites().list().execute()
    site_urls = [s["siteUrl"] for s in sites.get("siteEntry", [])]
    print(f"✅ GSC connected! Verified sites: {site_urls}")
    print(f"\nSet GSC_SITE_URL to one of the above, e.g.:")
    if site_urls:
        print(f'  export GSC_SITE_URL="{site_urls[0]}"')
except Exception as e:
    print(f"⚠️  Token saved but verification failed: {e}")
    print("The token should still work — try running gsc_client.py")
