from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# This will store the user's Seedr token after authorization
SEEDR_TOKEN = None

SEEDR_API_BASE = "https://www.seedr.cc/rest"


def seedr_request(endpoint, params=None):
    global SEEDR_TOKEN
    if not SEEDR_TOKEN:
        raise Exception("Seedr token not set. Call /authorize first.")

    if params is None:
        params = {}

    params["access_token"] = SEEDR_TOKEN
    url = f"{SEEDR_API_BASE}/{endpoint}"

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


@app.route("/")
def home():
    return jsonify({
        "name": "Seedr Stremio Addon",
        "status": "running",
        "authorize": "/authorize?token=YOUR_SEEDR_TOKEN",
        "manifest": "/manifest.json"
    })


# Step 1: User pastes their Seedr token here
# Example:
# https://stremthru-seedr-cc.onrender.com/authorize?token=PASTE_TOKEN
@app.route("/authorize")
def authorize():
    global SEEDR_TOKEN

    token = request.args.get("token")
    if not token:
        return jsonify({
            "error": "Missing token",
            "usage": "/authorize?token=YOUR_SEEDR_TOKEN"
        }), 400

    # Validate token by calling Seedr API
    try:
        r = requests.get(
            f"{SEEDR_API_BASE}/folder",
            params={"access_token": token},
            timeout=15
        )

        if r.status_code != 200:
            return jsonify({
                "error": "Invalid Seedr token",
                "details": r.text
            }), 401

        SEEDR_TOKEN = token

        return jsonify({
            "status": "authorized",
            "message": "Seedr token accepted successfully",
            "next": "/manifest.json"
        })

    except Exception as e:
        return jsonify({
            "error": "Authorization failed",
            "details": str(e)
        }), 500


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


@app.route("/catalog/movie/seedr.json")
def catalog():
    try:
        data = seedr_request("folder")

        metas = []
        for f in data.get("files", []):
            metas.append({
                "id": str(f["id"]),
                "type": "movie",
                "name": f["name"],
                "poster": "https://www.seedr.cc/favicon.ico"
            })

        return jsonify({"metas": metas})

    except Exception as e:
        return jsonify({
            "error": "Failed to load catalog",
            "details": str(e)
        }), 500


@app.route("/stream/movie/<file_id>.json")
def stream(file_id):
    try:
        # Get file download link
        data = seedr_request(f"file/{file_id}")

        url = data.get("url")
        if not url:
            return jsonify({"streams": []})

        return jsonify({
            "streams": [
                {
                    "title": "Seedr Cloud",
                    "url": url
                }
            ]
        })

    except Exception as e:
        return jsonify({
            "error": "Failed to get stream",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
