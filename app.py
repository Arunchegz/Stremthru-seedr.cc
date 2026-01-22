from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

# Seedr endpoints
SEEDR_DEVICE_URL = "https://www.seedr.cc/rest/device/add"
SEEDR_FOLDER_URL = "https://www.seedr.cc/rest/folder"
SEEDR_FILE_URL = "https://www.seedr.cc/rest/file"

# Global token storage (simple version)
access_token = None


# -----------------------
# Home
# -----------------------
@app.route("/")
def home():
    return jsonify({
        "name": "Seedr Stremio Addon",
        "status": "running",
        "authorize": "/authorize",
        "manifest": "/manifest.json",
        "catalog": "/catalog/movie/seedr.json",
        "stream": "/stream/movie/<id>.json"
    })


# -----------------------
# Seedr Device Authorization
# -----------------------
@app.route("/authorize")
def authorize():
    """
    Creates a new Seedr device and returns the device code.
    User must enter this code at https://www.seedr.cc/devices
    """
    global access_token
    try:
        r = requests.post(SEEDR_DEVICE_URL, timeout=10)
        r.raise_for_status()
        data = r.json()

        # Seedr gives token immediately
        access_token = data["token"]

        return jsonify({
            "message": "Go to https://www.seedr.cc/devices and enter this code",
            "user_code": data["code"],
            "access_token": access_token
        })
    except Exception as e:
        return jsonify({
            "error": "Seedr authorize failed",
            "details": str(e)
        }), 500


# -----------------------
# Stremio Manifest
# -----------------------
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


# -----------------------
# Catalog Endpoint
# -----------------------
@app.route("/catalog/movie/seedr.json")
def catalog():
    if not access_token:
        return jsonify({"error": "Not authorized. Visit /authorize first"}), 401

    try:
        r = requests.get(SEEDR_FOLDER_URL, params={
            "access_token": access_token
        }, timeout=10)
        r.raise_for_status()
        data = r.json()

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
        return jsonify({
            "error": "Failed to load catalog",
            "details": str(e)
        }), 500


# -----------------------
# Stream Endpoint
# -----------------------
@app.route("/stream/movie/<id>.json")
def stream(id):
    if not access_token:
        return jsonify({"streams": []})

    try:
        r = requests.get(SEEDR_FILE_URL, params={
            "access_token": access_token,
            "id": id
        }, timeout=10)
        r.raise_for_status()
        data = r.json()

        stream_url = data["url"]

        return jsonify({
            "streams": [
                {
                    "title": "Seedr Cloud",
                    "url": stream_url
                }
            ]
        })

    except Exception as e:
        return jsonify({
            "streams": [],
            "error": str(e)
        })


# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
