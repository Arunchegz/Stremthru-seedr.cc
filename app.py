from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seedrcc import Seedr
import os
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_client():
    return Seedr.from_device_code(os.environ["SEEDR_DEVICE_CODE"])


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


@app.get("/debug/files")
def debug_files():
    with get_client() as client:
        contents = client.list_contents()
        return [
            {
                "file_id": f.file_id,
                "folder_file_id": f.folder_file_id,
                "name": f.name,
                "size": f.size,
                "play_video": f.play_video
            }
            for f in contents.files
        ]


def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


@app.get("/stream/{type}/{id}.json")
def stream(type: str, id: str):
    streams = []

    try:
        with get_client() as client:
            contents = client.list_contents()

            for file in contents.files:
                if not file.play_video:
                    continue

                # Create streaming URL using Seedr API
                result = client.fetch_file(file.folder_file_id)

                streams.append({
                    "name": "Seedr.cc",
                    "title": file.name,
                    "url": result.url,
                    "behaviorHints": {
                        "notWebReady": False
                    }
                })

    except Exception as e:
        return {
            "streams": [],
            "error": str(e)
        }

    return {"streams": streams}
