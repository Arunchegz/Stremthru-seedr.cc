@app.route("/")
def home():
    return jsonify({
        "name": "Seedr Stremio Addon",
        "status": "running",
        "authorize": "/authorize",
        "poll": "/poll",
        "token": "/token"
    })
from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

SEEDR_CLIENT_ID = os.getenv("SEEDR_CLIENT_ID", "stremio-addon")

SEEDR_DEVICE_URL = "https://www.seedr.cc/oauth/device"
SEEDR_TOKEN_URL = "https://www.seedr.cc/oauth/token"

device_data = {}
access_token = None


@app.route("/authorize")
def authorize():
    try:
        resp = requests.post(SEEDR_DEVICE_URL, data={
            "client_id": SEEDR_CLIENT_ID,
            "scope": "user"
        }, timeout=10)

        print("Seedr status:", resp.status_code)
        print("Seedr response:", resp.text)

        resp.raise_for_status()
        data = resp.json()

        device_data.update(data)

        return jsonify({
            "message": "Go to https://www.seedr.cc/devices and enter this code",
            "user_code": data["user_code"],
            "device_code": data["device_code"],
            "verification_uri": data.get("verification_uri", "https://www.seedr.cc/devices"),
            "expires_in": data["expires_in"],
            "interval": data["interval"]
        })

    except Exception as e:
        return jsonify({
            "error": "Authorize failed",
            "details": str(e)
        }), 500


@app.route("/poll")
def poll():
    global access_token

    if "device_code" not in device_data:
        return jsonify({"error": "Visit /authorize first"}), 400

    try:
        resp = requests.post(SEEDR_TOKEN_URL, data={
            "client_id": SEEDR_CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_data["device_code"]
        }, timeout=10)

        print("Poll status:", resp.status_code)
        print("Poll response:", resp.text)

        data = resp.json()

        if "access_token" in data:
            access_token = data["access_token"]
            return jsonify({
                "status": "authorized",
                "access_token": access_token
            })

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "error": "Polling failed",
            "details": str(e)
        }), 500


@app.route("/token")
def token():
    if not access_token:
        return jsonify({"authorized": False})
    return jsonify({"authorized": True, "access_token": access_token})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)