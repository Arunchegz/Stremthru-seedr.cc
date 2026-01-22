from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

seedr_token = None

SEEDR_API = "https://www.seedr.cc/rest"

# ------------------------
# Home
# ------------------------
@app.route("/")
def home():
    return jsonify({
        "name": "Seedr Stremio Addon",
        "status": "running",
        "authorize": "/authorize?token=YOUR_SEEDR_TOKEN",
        "manifest": "/manifest.json"
    })


# ------------------------
# Authorize (manual token)
# ------------------------
@app.route("/authorize")
def authorize():
    global seedr_token

    token = request.args.get("token")
    if not token:
        return jsonify({
            "error": "Missing token",
            "usage": "/authorize?token=YOUR_SEEDR_TOKEN"
        }), 400

    # Validate token
    r = requests.get(f"{SEEDR_API}/folder", params={"access_token": token})

    if r.status_code != 200:
        return jsonify({
            "error": "Invalid token",
            "status": r.status_code,
            "response": r.text
        }), 401

    seedr_token = token

    return jsonify({
        "status": "authorized",
        "message": "Seedr token saved successfully"
    })


# ------------------------
# Manifest
# ------------------------
@app.route("/manifest.json")
def manifest():
    return jsonify({
        "id": "org.seedr.cloud",
        "version": "1.0.0",
        "name": "Seedr Cloud",
        "description": "Stream files from your Seedr.cc cloud",
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


# ------------------------
# Catalog
# ------------------------
@app.route("/catalog/movie/seedr.json")
def catalog():
    if not seedr_token:
        return jsonify({"metas": []})

    r = requests.get(f"{SEEDR_API}/folder", params={"access_token": seedr_token})
    data = r.json()

    metas = []

    for f in data.get("files", []):
        metas.append({
            "id": str(f["id"]),
            "type": "movie",
            "name": f["name"],
            "poster": "https://www.seedr.cc/favicon.ico"
        })

    return jsonify({"metas": metas})


# ------------------------
# Stream
# ------------------------
@app.route("/stream/movie/<id>.json")
def stream(id):
    if not seedr_token:
        return jsonify({"streams": []})

    r = requests.get(f"{SEEDR_API}/file/{id}", params={"access_token": seedr_token})
    data = r.json()

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


# ------------------------
# Run
# ------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
