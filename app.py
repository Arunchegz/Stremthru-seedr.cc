from flask import Flask, jsonify
import requests
import os
import time

app = Flask(__name__)

# -------------------------
# Global storage (simple)
# -------------------------
device_data = {}
access_token = None

SEEDR_DEVICE_ADD = "https://www.seedr.cc/rest/device/add"
SEEDR_DEVICE_CODE = "https://www.seedr.cc/rest/device/code"
SEEDR_FOLDER_API = "https://www.seedr.cc/rest/folder"
SEEDR_FILE_API = "https://www.seedr.cc/rest/file"

HEADERS = {
    "User-Agent": "Seedr-Stremio-Addon",
    "Accept": "application/json"
}


# -------------------------
# Home
# -------------------------
@app.route("/")
def home():
    return jsonify({
        "name": "Seedr Stremio Addon",
        "status": "running",
        "steps": {
            "1": "/authorize  → get device code",
            "2": "Open https://www.seedr.cc/devices and paste code",
            "3": "/poll → wait until authorized",
            "4": "/manifest.json → use addon in Stremio"
        }
    })


# -------------------------
# Create Device Code
# -------------------------
@app.route("/authorize")
def authorize():
    try:
        resp = requests.post(SEEDR_DEVICE_ADD, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        device_data["device_code"] = data["device_code"]
        device_data["user_code"] = data["user_code"]
        device_data["created"] = time.time()

        return jsonify({
            "message": "Go to https://www.seedr.cc/devices and paste this code",
            "user_code": data["user_code"],
            "device_code": data["device_code"]
        })

    except Exception as e:
        return jsonify({
            "error": "Seedr authorize failed",
            "details": str(e)
        }), 500


# -------------------------
# Poll for token
# -------------------------
@app.route("/poll")
def poll():
    global access_token

    if "device_code" not in device_data:
        return jsonify({"error": "Call /authorize first"}), 400

    try:
        resp = requests.get(
            SEEDR_DEVICE_CODE,
            params={"device_code": device_data["device_code"]},
            headers=HEADERS,
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        if "access_token" in data:
            access_token = data["access_token"]
            return jsonify({
                "authorized": True,
                "access_token": access_token
            })

        return jsonify({
            "authorized": False,
            "status": data
        })

    except Exception as e:
        return jsonify({
            "error": "Polling failed",
            "details": str(e)
        }), 500


# -------------------------
# Check token
# -------------------------
@app.route("/token")
def token():
    if not access_token:
        return jsonify({"authorized": False})
    return jsonify({"authorized": True, "access_token": access_token})


# -------------------------
# Stremio Manifest
# -------------------------
@app.route("/manifest.json")
def manifest():
    return jsonify({
        "id": "org.seedr.cloud",
        "version": "1.0.0",
        "name": "Seedr Cloud",
        "description": "Stream your Seedr.cc files directly",
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
# Catalog Endpoint
# -------------------------
@app.route("/catalog/movie/seedr.json")
def catalog():
    if not access_token:
        return jsonify({"error": "Not authorized, visit /authorize"}), 401

    try:
        resp = requests.get(
            SEEDR_FOLDER_API,
            params={"access_token": access_token},
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        metas = []
        for f in data.get("files", []):
            metas.append({
                "id": str(f["id"]),
                "type": "movie",
                "name": f["name"],
                "poster": "https://seedr.cc/favicon.ico"
            })

        return jsonify({"metas": metas})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# Stream Endpoint
# -------------------------
@app.route("/stream/movie/<id>.json")
def stream(id):
    if not access_token:
        return jsonify({"error": "Not authorized"}), 401

    try:
        resp = requests.get(
            SEEDR_FILE_API,
            params={
                "access_token": access_token,
                "file_id": id
            },
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        return jsonify({
            "streams": [
                {
                    "title": "Seedr Cloud",
                    "url": data["url"]
                }
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
