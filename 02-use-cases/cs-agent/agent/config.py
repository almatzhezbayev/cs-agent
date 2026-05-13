from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("CS_AGENT_DATA_DIR", BASE_DIR / ".data"))
LOCAL_DATA_DIR = Path(os.getenv("CS_AGENT_LOCAL_DATA_DIR", BASE_DIR / "data"))
GOOGLE_STATE_PATH = Path(
    os.getenv("CS_AGENT_GOOGLE_STATE_PATH", DATA_DIR / "google_oauth_state.json")
)
GOOGLE_TOKEN_PATH = Path(
    os.getenv("CS_AGENT_GOOGLE_TOKEN_PATH", DATA_DIR / "google_tokens.json")
)
GOOGLE_CREDENTIALS_PATH = Path(
    os.getenv("GOOGLE_CLIENT_SECRETS_FILE", BASE_DIR / "credentials.json")
)
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
)
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
CUSTOMERS_DATA_PATH = Path(
    os.getenv("CS_AGENT_CUSTOMERS_DATA_PATH", LOCAL_DATA_DIR / "customers.json")
)
WARRANTIES_DATA_PATH = Path(
    os.getenv("CS_AGENT_WARRANTIES_DATA_PATH", LOCAL_DATA_DIR / "warranties.json")
)
