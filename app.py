from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seedrcc import Seedr
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_client():
    with open("seedr_token.json", "r") as f:
        data = json.load(f)

    device_code = data["device_code"]
    return Seedr.from_device_code(device_code)


@app.get("/manifest.json")
def manifest():
    return {
        "id": "org.seedrcc.stremio",
        "version": "1.0.0",
        "name": "Seedr.cc Personal Addon",
        "description": "Stream your Seedr.cc files directly in Stremio",
        "resources": ["stream"],
        "types": ["movie", "series", "other"],
        "catalogs": []
    }


@app.get("/stream/{type}/{id}.json")
def stream(type: str, id: str):
    streams = []

    with get_client() as client:
        contents = client.list_contents()

        for file in contents.files:
            if str(file.file_id) == str(id) and file.play_video:
                url = client.fetch_file(file.file_id)
                streams.append({
                    "name": file.name,
                    "title": file.name,
                    "url": url
                })

    return {"streams": streams}
