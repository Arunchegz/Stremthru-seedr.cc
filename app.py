from flask import Flask, jsonify
from seedr_client import SeedrClient
import os

app = Flask(__name__)

SEEDR_TOKEN = os.getenv("SEEDR_TOKEN")
seedr = SeedrClient(SEEDR_TOKEN)


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
    data = seedr.list_root()
    metas = []

    for f in data.get("files", []):
        metas.append({
            "id": str(f["id"]),
            "type": "movie",
            "name": f["name"],
            "poster": "https://seedr.cc/favicon.ico"
        })

    return jsonify({"metas": metas})


@app.route("/stream/movie/<id>.json")
def stream(id):
    url = seedr.get_stream_url(id)
    return jsonify({
        "streams": [
            {
                "title": "Seedr Cloud",
                "url": url
            }
        ]
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)