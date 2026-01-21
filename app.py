from flask import Flask, jsonify, request
import requests
import os
import time

app = Flask(__name__)

SEEDR_CLIENT_ID = os.getenv("SEEDR_CLIENT_ID", "stremio-addon")
SEEDR_DEVICE_URL = "https://www.seedr.cc/oauth/device/code"
SEEDR_TOKEN_URL = "https://www.seedr.cc/oauth/token"

# In-memory storage (later you can store in DB)
device_data = {}
access_token = None


@app.route("/authorize")
def authorize():
    """
    Step 1: Ask Seedr for a device code
    """
    resp = requests.post(SEEDR_DEVICE_URL, data={
        "client_id": SEEDR_CLIENT_ID,
        "scope": "user"
    })

    if resp.status_code != 200:
        return jsonify({"error": "Failed to get device code", "detail": resp.text}), 500

    data = resp.json()
    device_data.update(data)

    return jsonify({
        "message": "Go to https://www.seedr.cc/devices and enter this code",
        "device_code": data["device_code"],
        "user_code": data["user_code"],
        "verification_uri": data["verification_uri"],
        "expires_in": data["expires_in"],
        "interval": data["interval"]
    })


@app.route("/poll")
def poll():
    """
    Step 2: Poll Seedr until user authorizes device
    """
    global access_token

    if "device_code" not in device_data:
        return jsonify({"error": "No device code found. Visit /authorize first."}), 400

    resp = requests.post(SEEDR_TOKEN_URL, data={
        "client_id": SEEDR_CLIENT_ID,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device_data["device_code"]
    })

    data = resp.json()

    if "access_token" in data:
        access_token = data["access_token"]
        return jsonify({
            "status": "authorized",
            "access_token": access_token
        })

    return jsonify(data)


@app.route("/token")
def token():
    """
    Check if token is stored
    """
    if not access_token:
        return jsonify({"authorized": False})
    return jsonify({"authorized": True, "access_token": access_token})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)