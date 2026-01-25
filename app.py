from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seedrcc import Seedr
import os
import re
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_client():
    return Seedr.from_device_code(os.environ["SEEDR_DEVICE_CODE"])


def normalize(text: str):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def get_movie_title(imdb_id: str):
    url = f"https://v3-cinemeta.strem.io/meta/movie/{imdb_id}.json"
    data = requests.get(url, timeout=10).json()
    meta = data.get("meta", {})
    title = meta.get("name", "")
    year = str(meta.get("year", ""))
    return title, year


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


@app.get("/stream/{type}/{id}.json")
def stream(type: str, id: str):
    streams = []

    if type != "movie":
        return {"streams": []}

    try:
        # 1. Get movie title from IMDb
        movie_title, movie_year = get_movie_title(id)
        norm_title = normalize(movie_title)

        with get_client() as client:
            contents = client.list_contents()

            for file in contents.files:
                if not file.play_video:
                    continue

                fname = normalize(file.name)

                # 2. Match movie title + optionally year
                if norm_title in fname and (movie_year in file.name):
                    # 3. Fetch real streaming URL
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
