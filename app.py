from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seedrcc import Seedr
import os
import re
import requests

app = FastAPI()

# CORS for Stremio + browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Seedr Client
# -------------------------
def get_client():
    return Seedr.from_device_code(os.environ["SEEDR_DEVICE_CODE"])


# -------------------------
# Helpers
# -------------------------
def normalize(text: str):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def get_movie_title(imdb_id: str):
    url = f"https://v3-cinemeta.strem.io/meta/movie/{imdb_id}.json"
    data = requests.get(url, timeout=10).json()
    meta = data.get("meta", {})
    title = meta.get("name", "")
    year = str(meta.get("year", ""))
    return title, year


def walk_files(client, folder_id=None):
    """
    Recursively walk all files and folders in Seedr.
    """
    contents = client.list_contents(folder_id=folder_id)

    for f in contents.files:
        yield f

    for folder in contents.folders:
        yield from walk_files(client, folder.id)


# -------------------------
# Manifest
# -------------------------
@app.get("/manifest.json")
def manifest():
    return {
        "id": "org.seedrcc.stremio",
        "version": "1.1.0",
        "name": "Seedr.cc Personal Addon",
        "description": "Browse and stream your Seedr.cc files directly in Stremio",
        "resources": ["stream", "catalog", "meta"],
        "types": ["movie"],
        "catalogs": [
            {
                "type": "movie",
                "id": "seedr",
                "name": "My Seedr Library"
            }
        ]
    }


# -------------------------
# Debug (see everything in Seedr)
# -------------------------
@app.get("/debug/files")
def debug_files():
    with get_client() as client:
        return [
            {
                "file_id": f.file_id,
                "folder_file_id": f.folder_file_id,
                "name": f.name,
                "size": f.size,
                "play_video": f.play_video,
            }
            for f in walk_files(client)
        ]


# -------------------------
# Catalog → Shows in Stremio as "My Seedr Library"
# -------------------------
@app.get("/catalog/movie/seedr.json")
def catalog():
    metas = []

    with get_client() as client:
        for file in walk_files(client):
            if not file.play_video:
                continue

            metas.append({
                "id": str(file.folder_file_id),
                "type": "movie",
                "name": file.name,
                "poster": getattr(file, "thumb", None),
            })

    return {"metas": metas}


# -------------------------
# Meta → When clicking a catalog item
# -------------------------
@app.get("/meta/movie/{id}.json")
def meta(id: str):
    with get_client() as client:
        for file in walk_files(client):
            if str(file.folder_file_id) == id:
                return {
                    "meta": {
                        "id": id,
                        "type": "movie",
                        "name": file.name,
                        "poster": getattr(file, "thumb", None),
                        "description": "From your Seedr.cc account",
                    }
                }
    return {"meta": None}


# -------------------------
# Stream → When pressing Play
# -------------------------
@app.get("/stream/{type}/{id}.json")
def stream(type: str, id: str):
    streams = []

    if type != "movie":
        return {"streams": []}

    try:
        # This ID is folder_file_id from Seedr
        with get_client() as client:
            for file in walk_files(client):
                if str(file.folder_file_id) == id and file.play_video:
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
