"""
Warif Framework - Sensor Data Integration Service
==================================================
Project: Warif Digital Twin Framework (وارِف)
Course: CSAI-471 | Umm Al-Qura University
"""

import requests
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# ─────────────────────────────────────────────
# LOAD ENV
# ─────────────────────────────────────────────
load_dotenv()

HAJJ_EMAIL    = os.getenv("HAJJ_EMAIL")
HAJJ_PASSWORD = os.getenv("HAJJ_PASSWORD")

SOURCE_BASE_URL = "https://orangepi.baitguests2.com"
LOGIN_URL       = "https://orangepi.baitguests2.com/login/"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("warif.integration")


# ─────────────────────────────────────────────
# TOKEN MANAGER
# ─────────────────────────────────────────────

class TokenManager:
    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None

    def _is_expired(self) -> bool:
        if self._token is None or self._expires_at is None:
            return True
        return datetime.now() >= (self._expires_at - timedelta(minutes=5))

    def _login(self) -> None:
        email    = os.getenv("HAJJ_EMAIL")
        password = os.getenv("HAJJ_PASSWORD")

        if not email or not password:
            raise HTTPException(
                status_code=500,
                detail="HAJJ_EMAIL or HAJJ_PASSWORD not set in .env"
            )

        logger.info("🔐 Logging in to Hajj API...")

        try:
            response = requests.post(
                LOGIN_URL,
                json={"email": email, "password": password},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            self._token      = data.get("data", {}).get("token", {}).get("access")
            self._expires_at = datetime.now() + timedelta(hours=23)

            logger.info("✅ Login successful.")

        except requests.exceptions.HTTPError:
            logger.error(f"❌ Login failed: {response.text}")
            raise HTTPException(
                status_code=401,
                detail=f"Login failed: {response.text}"
            )
        except requests.exceptions.ConnectionError:
            raise HTTPException(status_code=503, detail="Auth server unreachable.")

    def get_token(self) -> str:
        if self._is_expired():
            self._login()
        return self._token


token_manager = TokenManager()


# ─────────────────────────────────────────────
# FETCH HELPER
# ─────────────────────────────────────────────

def fetch_from_source(endpoint: str, params: Optional[dict] = None) -> dict:
    url     = f"{SOURCE_BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token_manager.get_token()}",
        "Accept":        "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        logger.info(f"✅ Fetched /{endpoint} — {response.status_code}")
        return response.json()

    except requests.exceptions.HTTPError:
        if response.status_code == 401:
            token_manager._token      = None
            token_manager._expires_at = None
            raise HTTPException(status_code=401, detail="Token rejected. Retry.")
        raise HTTPException(status_code=response.status_code, detail=response.text)

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Source API unreachable.")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Source API timed out.")


# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="Warif Sensor Integration API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://warif.netlify.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "project":   "Warif Digital Twin Framework | وارِف",
        "status":    "running",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/health")
def health_check():
    try:
        fetch_from_source("time/")
        return {
            "status":     "ok",
            "source_api": "reachable",
            "token":      "valid",
            "checked_at": datetime.now().isoformat(),
        }
    except HTTPException as e:
        return {"status": "error", "detail": e.detail}


@app.get("/api/sensors")
def get_sensors(is_arafa: bool = False, is_live: bool = True):
    data = fetch_from_source("sensor/", params={
        "is_arafa": is_arafa,
        "is_live":  is_live,
    })
    return {
        "source":    "hajj.aiqualitysolutions.com",
        "timestamp": datetime.now().isoformat(),
        "data":      data,
    }


@app.get("/api/time")
def get_server_time():
    return fetch_from_source("time/")


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("🌱 Warif Integration Service starting...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
