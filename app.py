from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seedrcc import Seedr
import os
import re
import requests

app = FastAPI()

# Allow Stremio + browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Seedr Client
# -----------------------

def get_client():
    return Seedr.from_device_code(os.environ["SEEDR_DEVICE_CODE"])


# -----------------------
# Helpers
# -----------------------

def normalize(text: str):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def get_movie_title(imdb_id: str):
    """
    Get movie title + year from Stremio Cinemeta using IMDb ID
    """
    url = f"https://v3-cinemeta.strem.io/meta/movie/{imdb_id}.json"
    data = requests.get(url, timeout=10).json()
    meta = data.get("meta", {})
    title = meta.get("name", "")
    year = str(meta.get("year", ""))
    return title, year


def walk_files(client, folder_id=None):
    """
    Recursively walk through Seedr root and all subfolders
    and yield every file found.
    """
    contents = client.list_contents(folder_id=folder_id)

    for f in contents.files:
        yield f

    for folder in contents.folders:
        yield from walk_files(client, folder.id)


# -----------------------
# Manifest
# -----------------------

@app.get("/manifest.json")
def manifest():
    return {
        "id": "org.seedrcc.stremio",
        "version": "1.0.0",
        "name": "Seedr.cc Personal Addon",
        "description": "Stream your Seedr.cc files directly in Stremio",
        "resources": ["stream"],
        "types": ["movie"],
        "catalogs": []
    }


# -----------------------
# Debug: See all files Seedr sees (including inside folders)
# -----------------------

@app.get("/debug/files")
def debug_files():
    with get_client() as client:
        return [
            {
                "file_id": f.file_id,
                "folder_file_id": f.folder_file_id,
                "name": f.name,
                "size": f.size,
                "play_video": f.play_video
            }
            for f in walk_files(client)
        ]


# -----------------------
# Stream endpoint (used by Stremio)
# -----------------------

@app.get("/stream/{type}/{id}.json")
def stream(type: str, id: str):
    streams = []

    if type != "movie":
        return {"streams": []}

    try:
        # 1. Get movie title + year from IMDb
        movie_title, movie_year = get_movie_title(id)
        norm_title = normalize(movie_title)

        with get_client() as client:
            # 2. Walk ALL files including inside folders
            for file in walk_files(client):
                if not file.play_video:
                    continue

                fname = normalize(file.name)

                # 3. Match by title and year
                if norm_title in fname and movie_year in file.name:
                    # 4. Fetch real streaming URL from Seedr
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
        # Never crash Stremio
        return {
            "streams": [],
            "error": str(e)
        }

    return {"streams": streams}
