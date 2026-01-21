import os
import requests
from flask import Flask, jsonify
from seedr_client import SeedrClient

app = Flask(__name__)

# =========================
# Seedr OAuth (Device Flow)
# =========================

SEEDR_DEVICE_CODE_URL = "https://www.seedr.cc/oauth/device/code"
SEEDR_TOKEN_URL = "https://www.seedr.cc/oauth/token"

# Seedr public client id (Seedr uses "seedr" as client_id)
SEEDR_CLIENT_ID = "seedr"

# In-memory storage for device sessions and tokens
# (For now, simple dict. Later you can move this to DB or Redis)
device_sessions = {}
user_tokens = {}

# -------------------------
# Step 1: Get device code
# -------------------------
@app.route("/authorize")
def authorize():
    r = requests.post(
        SEEDR_DEVICE_CODE_URL,
        data={
            "client_id": SEEDR_CLIENT_ID,
            "scope": "user"
        }
    )

    data = r.json()

    # Save session info
    device_sessions[data["device_code"]] = data

    return jsonify({
        "message": "Go to https://www.seedr.cc/devices and enter this code",
        "user_code": data["user_code"],
        "device_code": data["device_code"],
        "verification_uri": data["verification_uri"],
        "expires_in": data["expires_in"],
        "interval": data.get("interval", 5)
    })


# -------------------------
# Step 2: Poll for token
# -------------------------
@app.route("/poll/<device_code>")
def poll(device_code):
    if device_code not in device_sessions:
        return jsonify({"error": "Invalid device code"}), 400

    r = requests.post(
        SEEDR_TOKEN_URL,
        data={
            "client_id": SEEDR_CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code
        }
    )

    data = r.json()

    # Still waiting for user authorization
    if "error" in data:
        return jsonify(data)

    # Authorized successfully
    access_token = data["access_token"]
    user_tokens[device_code] = access_token

    return jsonify({
        "status": "authorized",
        "access_token": access_token,
        "token_type": data.get("token_type"),
        "expires_in": data.get("expires_in")
    })


# =========================
# Stremio Addon Endpoints
# =========================

# Manifest
@app.route("/manifest.json")
def manifest():
    return jsonify({
        "id": "org.seedr.cloud",
        "version": "1.0.0",
        "name": "Seedr Cloud",
        "description": "Stream your Seedr.cc cloud files directly in Stremio",
        "resources": ["catalog", "stream"],
        "types": ["movie"],
        "catalogs": [
            {
                "type": "movie",
                "id": "seedr",
                "name": "Seedr Files"
            }
        ]
    })


# -------------------------
# Catalog
# -------------------------
# For now this uses the *latest authorized* token.
# Later we can bind device_code to users properly.
@app.route("/catalog/movie/seedr.json")
def catalog():
    if not user_tokens:
        return jsonify({
            "error": "No Seedr account authorized yet. Visit /authorize first."
        }), 401

    # Take the last authorized token
    access_token = list(user_tokens.values())[-1]
    seedr = SeedrClient(access_token)

    root = seedr.list_root()

    metas = []
    for folder in root.get("folders", []):
        metas.append({
            "id": f"folder:{folder['id']}",
            "type": "movie",
            "name": folder["name"],
            "poster": "https://seedr.cc/favicon.ico"
        })

    return jsonify({"metas": metas})


# -------------------------
# Stream
# -------------------------
@app.route("/stream/movie/<id>.json")
def stream(id):
    if not user_tokens:
        return jsonify({
            "streams": [],
            "error": "No Seedr account authorized yet. Visit /authorize first."
        }), 401

    access_token = list(user_tokens.values())[-1]
    seedr = SeedrClient(access_token)

    streams = []

    # Folder: list all files inside
    if id.startswith("folder:"):
        folder_id = id.replace("folder:", "")
        data = seedr.list_folder(folder_id)

        for f in data.get("files", []):
            streams.append({
                "title": f["name"],
                "url": seedr.get_stream_url(f["id"])
            })

    else:
        # Direct file id
        streams.append({
            "title": "Seedr Cloud",
            "url": seedr.get_stream_url(id)
        })

    return jsonify({"streams": streams})


# =========================
# App Start
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)