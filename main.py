import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from seedrcc import Seedr, Token

TOKEN_FILE = "seedr_token.json"

app = FastAPI()

seedr_client: Seedr | None = None


# ---------------------------
# Token storage helpers
# ---------------------------

def save_token(token: Token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token.to_json())


def load_token() -> Token | None:
    if os.path.exists(TOKEN_FILE):
        return Token.from_json(open(TOKEN_FILE).read())
    return None


# ---------------------------
# Seedr initialization
# ---------------------------

def init_seedr():
    global seedr_client

    token = load_token()
    if token:
        seedr_client = Seedr(token, on_token_refresh=save_token)
        return True

    return False


# ---------------------------
# Device auth endpoints
# ---------------------------

@app.get("/seedr/device-code")
def get_device_code():
    """
    Step 1: Call this to get a user code.
    """
    codes = Seedr.get_device_code()
    return {
        "device_code": codes.device_code,
        "user_code": codes.user_code,
        "verification_url": codes.verification_url,
        "message": f"Go to {codes.verification_url} and enter code {codes.user_code}"
    }


@app.get("/seedr/authorize/{device_code}")
def authorize_device(device_code: str):
    """
    Step 2: Call this AFTER approving device on seedr.cc/devices
    """
    global seedr_client

    client = Seedr.from_device_code(device_code, on_token_refresh=save_token)
    save_token(client.token)
    seedr_client = client

    return {"status": "authorized"}


# ---------------------------
# Stremio manifest
# ---------------------------

@app.get("/manifest.json")
def manifest():
    return {
        "id": "org.seedr.streamer",
        "version": "1.0.0",
        "name": "Seedr Streamer",
        "description": "Stream files directly from Seedr",
        "types": ["movie", "series", "other"],
        "resources": ["stream"],
        "catalogs": []
    }


# ---------------------------
# Stream endpoint
# ---------------------------

@app.get("/stream/{type}/{id}.json")
def stream(type: str, id: str):
    if not seedr_client:
        raise HTTPException(400, "Seedr not authorized")

    try:
        folder = seedr_client.list_contents()
    except Exception as e:
        raise HTTPException(500, f"Seedr API error: {e}")

    streams = []

    for f in folder.files:
        if f.name.lower().endswith((".mp4", ".mkv", ".avi", ".mov", ".webm")):
            try:
                link = seedr_client.fetch_file(f.folder_file_id)

                streams.append({
                    "name": "Seedr",
                    "title": f.name,
                    "url": link.url
                })
            except Exception as e:
                print("Failed to fetch file:", e)

    return {"streams": streams}


# ---------------------------
# Startup
# ---------------------------

@app.on_event("startup")
def startup_event():
    init_seedr()
