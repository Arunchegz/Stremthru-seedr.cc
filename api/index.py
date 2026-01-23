from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

# Ensure you set this in Vercel Dashboard -> Settings -> Environment Variables
SEEDR_TOKEN = os.getenv("SEEDR_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {SEEDR_TOKEN}",
    "Accept": "application/json"
}

VIDEO_EXTS = (".mp4", ".mkv", ".avi", ".mov", ".webm")

@app.route("/manifest.json")
def manifest():
    return jsonify({
        "id": "org.seedr.streamer",
        "version": "1.0.0",
        "name": "Seedr Streamer",
        "description": "Stream existing Seedr files",
        "types": ["movie", "series"],
        "resources": ["stream"],
        "catalogs": []
    })

@app.route("/stream/<type>/<id>.json")
def stream(type, id):
    # 1. Get folder contents
    folder_url = "https://www.seedr.cc/rest/folder"
    r = requests.get(folder_url, headers=HEADERS)
    
    if r.status_code != 200:
        return jsonify({"streams": []})

    data = r.json()
    streams = []

    # 2. Find videos and get URLs
    # Optimization: In a real scenario, you'd match 'id' (IMDB ID) to a file name
    for f in data.get("files", []):
        if f["name"].lower().endswith(VIDEO_EXTS):
            # Fetch the stream URL only for relevant files
            file_url_api = f"https://www.seedr.cc/rest/file/{f['id']}"
            file_info = requests.get(file_url_api, headers=HEADERS).json()
            
            if "url" in file_info:
                streams.append({
                    "name": "Seedr",
                    "title": f["name"],
                    "url": file_info["url"]
                })

    return jsonify({"streams": streams})

# This is required for Vercel to treat this as a Serverless Function
if __name__ == "__main__":
    app.run(debug=True)
