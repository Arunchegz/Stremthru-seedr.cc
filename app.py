from flask import Flask, jsonify, request
from dotenv import load_dotenv
import requests
import os
import secrets
import time

load_dotenv()

app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================
SEEDR_COOKIE = os.getenv("SEEDR_COOKIE", "").strip()

SEEDR_FOLDER_API = "https://www.seedr.cc/rest/folder"
SEEDR_FILE_API = "https://www.seedr.cc/rest/file"

# Fake OAuth storage (like MediaFusion)
# device_code -> {created, authorized, token}
device_codes = {}

# =====================================================
# HEADERS (Browser-like to avoid Cloudflare)
# =====================================================
def seedr_headers():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.seedr.cc/",
        "Origin": "https://www.seedr.cc",
        "Cookie": SEEDR_COOKIE
    }

# =====================================================
# HOME
# =====================================================
@app.route("/")
def home():
    return jsonify({
        "name": "Seedr Cloud (MediaFusion style auth)",
        "status": "running",
        "flow": {
            "1": "GET /get-device-code",
            "2": "POST /authorize with device_code",
            "3": "Receive token",
            "4": "Use token in headers: Authorization: Bearer <token>",
            "5": "Use /manifest.json in Stremio"
        }
    })

# =====================================================
# TEST SEEDR COOKIE
# =====================================================
@app.route("/test-seedr")
def test_seedr():
    if not SEEDR_COOKIE:
        return jsonify({"error": "SEEDR_COOKIE not set"}), 500

    try:
        r = requests.get(SEEDR_FOLDER_API, headers=seedr_headers(), timeout=15)
        return jsonify({
            "status_code": r.status_code,
            "content_type": r.headers.get("Content-Type"),
            "response_preview": r.text[:500]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# DEVICE CODE (Your own, like MediaFusion)
# =====================================================
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
        "message": "Use this code in POST /authorize"
    })

# =====================================================
# AUTHORIZE (Exchange device code for token)
# =====================================================
@app.route("/authorize", methods=["POST"])
def authorize():
    data = request.json or {}
    code = data.get("device_code")

    if not code or code not in device_codes:
        return jsonify({"error": "Invalid device code"}), 400

    token = secrets.token_hex(32)
    device_codes[code]["authorized"] = True
    device_codes[code]["token"] = token

    return jsonify({
        "success": True,
        "token": token
    })

# =====================================================
# TOKEN CHECK
# =====================================================
def check_token(req):
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth.replace("Bearer ", "")
    return any(v["token"] == token for v in device_codes.values())

# =====================================================
# STREMIO MANIFEST
# =====================================================
@app.route("/manifest.json")
def manifest():
    return jsonify({
        "id": "org.seedr.cloud",
        "version": "1.0.0",
        "name": "Seedr Cloud",
        "description": "Stream your Seedr.cc files directly (MediaFusion style auth)",
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

# =====================================================
# CATALOG
# =====================================================
@app.route("/catalog/movie/seedr.json")
def catalog():
    if not check_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    r = requests.get(SEEDR_FOLDER_API, headers=seedr_headers(), timeout=15)

    try:
        data = r.json()
    except:
        return jsonify({
            "error": "Seedr returned non-JSON response",
            "status_code": r.status_code,
            "preview": r.text[:300]
        }), 500

    metas = []
    for f in data.get("files", []):
        metas.append({
            "id": str(f["id"]),
            "type": "movie",
            "name": f["name"],
            "poster": "https://seedr.cc/favicon.ico"
        })

    return jsonify({"metas": metas})

# =====================================================
# STREAM
# =====================================================
@app.route("/stream/movie/<id>.json")
def stream(id):
    if not check_token(request):
        return jsonify({"error": "Unauthorized"}), 401

    r = requests.get(
        SEEDR_FILE_API,
        params={"file_id": id},
        headers=seedr_headers(),
        timeout=15
    )

    try:
        data = r.json()
    except:
        return jsonify({
            "error": "Seedr returned non-JSON response",
            "status_code": r.status_code,
            "preview": r.text[:300]
        }), 500

    return jsonify({
        "streams": [
            {
                "title": "Seedr Cloud",
                "url": data.get("url")
            }
        ]
    })

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
