from flask import Flask, jsonify, Response
import requests
import os
import time

app = Flask(__name__)

# =======================
# CONFIG
# =======================

SEEDR_CLIENT_ID = os.getenv("SEEDR_CLIENT_ID", "stremio-addon")
SEEDR_DEVICE_URL = "https://www.seedr.cc/oauth/device"
SEEDR_TOKEN_URL = "https://www.seedr.cc/oauth/token"
SEEDR_API_BASE = "https://www.seedr.cc/rest"

device_data = {}
access_token = None


# =======================
# BASIC TEST
# =======================

@app.route("/ping")
def ping():
    return "OK"


@app.route("/")
def home():
    return jsonify({
        "name": "Seedr Stremio Addon",
        "status": "running",
        "authorize": "/authorize",
        "poll": "/poll",
        "token": "/token"
    })


# =======================
# STREMIO MANIFEST
# =======================

@app.route("/manifest.json")
def manifest():
    data = {
        "id": "org.seedr.stremio",
        "version": "1.0.0",
        "name": "Seedr Cloud",
        "description": "Stream your Seedr.cc cloud files in Stremio",
        "resources": ["catalog", "stream"],
        "types": ["movie"],
        "catalogs": [
            {
                "type": "movie",
                "id": "seedr",
                "name": "Seedr Files"
            }
        ]
    }

    return Response(
        response=jsonify(data).get_data(as_text=True),
        mimetype="application/json"
    )


# =======================
# SEEDR DEVICE OAUTH
# =======================

@app.route("/authorize")
def authorize():
    global device_data

    try:
        r = requests.post(SEEDR_DEVICE_URL, data={
            "client_id": SEEDR_CLIENT_ID,
            "scope": "user"
        }, timeout=10)

        r.raise_for_status()
        data = r.json()
        device_data = data

        return jsonify({
            "message": "Go to https://www.seedr.cc/devices and enter this code",
            "user_code": data["user_code"],
            "device_code": data["device_code"],
            "verification_uri": "https://www.seedr.cc/devices",
            "expires_in": data["expires_in"],
            "interval": data["interval"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/poll")
def poll():
    global access_token

    if "device_code" not in device_data:
        return jsonify({"error": "Visit /authorize first"}), 400

    try:
        r = requests.post(SEEDR_TOKEN_URL, data={
            "client_id": SEEDR_CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_data["device_code"]
        }, timeout=10)

        data = r.json()

        if "access_token" in data:
            access_token = data["access_token"]
            return jsonify({
                "status": "authorized",
                "access_token": access_token
            })

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/token")
def token():
    if not access_token:
        return jsonify({"authorized": False})
    return jsonify({"authorized": True, "access_token": access_token})


# =======================
# SEEDR API HELPERS
# =======================

def seedr_headers():
    return {"Authorization": f"Bearer {access_token}"}


def seedr_list_root():
    r = requests.get(f"{SEEDR_API_BASE}/folder", headers=seedr_headers())
    r.raise_for_status()
    return r.json()


def seedr_get_file(id):
    r = requests.get(f"{SEEDR_API_BASE}/file/{id}", headers=seedr_headers())
    r.raise_for_status()
    return r.json()


# =======================
# STREMIO CATALOG
# =======================

@app.route("/catalog/movie/seedr.json")
def catalog():
    if not access_token:
        return jsonify({"metas": []})

    data = seedr_list_root()
    metas = []

    for f in data.get("files", []):
        metas.append({
            "id": str(f["id"]),
            "type": "movie",
            "name": f["name"],
            "poster": "https://seedr.cc/favicon.ico"
        })

    return jsonify({"metas": metas})


# =======================
# STREMIO STREAM
# =======================

@app.route("/stream/movie/<id>.json")
def stream(id):
    if not access_token:
        return jsonify({"streams": []})

    file = seedr_get_file(id)
    return jsonify({
        "streams": [
            {
                "title": "Seedr Cloud",
                "url": file["url"]
            }
        ]
    })


# =======================
# RUN
# =======================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
