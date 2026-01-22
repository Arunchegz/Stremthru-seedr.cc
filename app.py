from flask import Flask, jsonify, request
import requests
import os
import secrets
import time

app = Flask(__name__)

# -------------------------
# CONFIG
# -------------------------
SEEDR_COOKIE = os.getenv("SEEDR_COOKIE")

SEEDR_FOLDER_API = "https://www.seedr.cc/rest/folder"
SEEDR_FILE_API = "https://www.seedr.cc/rest/file"

# Your fake OAuth storage
device_codes = {}  # code → {created, authorized, token}

def seedr_headers():
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Cookie": SEEDR_COOKIE
    }

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return jsonify({
        "name": "Seedr Stremio Addon",
        "status": "running",
        "steps": {
            "1": "GET /get-device-code",
            "2": "Enter code in /authorize",
            "3": "Receive token",
            "4": "Use token in Authorization: Bearer <token>",
            "5": "Use /manifest.json in Stremio"
        }
    })

# -------------------------
# DEVICE CODE (like MediaFusion)
# -------------------------
@app.route("/get-device-code")
def get_device_code():
    code = secrets.token_hex(4).upper()
    device_codes[code] = {
        "created": time.time(),
        "authorized": False,
        "token": None
    }
    return jsonify({
        "device_code": code,
        "message": "Use this code in /authorize"
    })

# -------------------------
# AUTHORIZE (fake OAuth)
# -------------------------
@app.route("/authorize", methods=["POST"])
def authorize():
    data = request.json
    code = data.get("device_code")

    if code not in device_codes:
        return jsonify({"error": "Invalid device code"}), 400

    token = secrets.token_hex(32)
    device_codes[code]["authorized"] = True
    device_codes[code]["token"] = token

    return jsonify({
        "success": True,
        "token": token
    })

# -------------------------
# TOKEN CHECK
# -------------------------
def check_token(req):
    auth = req.headers.get("Authorization")
    if not auth:
        return False
    token = auth.replace("Bearer ", "")
    return any(v["token"] == token for v in device_codes.values())

# -------------------------
# STREMIO MANIFEST
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
# CATALOG
# -------------------------
@app.route("/catalog/movie/seedr.json")
def catalog():
    if not check_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    r = requests.get(SEEDR_FOLDER_API, headers=seedr_headers())
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

# -------------------------
# STREAM
# -------------------------
@app.route("/stream/movie/<id>.json")
def stream(id):
    if not check_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    r = requests.get(
        SEEDR_FILE_API,
        params={"file_id": id},
        headers=seedr_headers()
    )
    data = r.json()

    return jsonify({
        "streams": [
            {
                "title": "Seedr Cloud",
                "url": data["url"]
            }
        ]
    })

# -------------------------
# TEST SEEDR LOGIN
# -------------------------
@app.route("/test-seedr")
def test_seedr():
    r = requests.get(SEEDR_FOLDER_API, headers=seedr_headers())
    return jsonify(r.json())

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
