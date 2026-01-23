from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

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
        "description": "Stream existing Seedr files in Stremio",
        "types": ["movie", "series", "other"],
        "resources": ["stream"],
        "catalogs": []
    })


def list_files():
    url = "https://www.seedr.cc/rest/folder"
    r = requests.get(url, headers=HEADERS)
    return r.json()


def find_video_files(data):
    videos = []
    for f in data.get("files", []):
        if f["name"].lower().endswith(VIDEO_EXTS):
            videos.append(f)
    return videos


def get_stream_url(file_id):
    url = f"https://www.seedr.cc/rest/file/{file_id}"
    r = requests.get(url, headers=HEADERS)
    return r.json()["url"]


@app.route("/stream/<type>/<id>.json")
def stream(type, id):
    data = list_files()
    videos = find_video_files(data)

    streams = []
    for v in videos:
        url = get_stream_url(v["id"])
        streams.append({
            "name": "Seedr",
            "title": v["name"],
            "url": url
        })

    return jsonify({"streams": streams})
