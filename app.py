from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seedrcc import Seedr
import os

app = FastAPI()

# Allow Stremio + browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client():
    device_code = os.environ["SEEDR_DEVICE_CODE"]
    return Seedr.from_device_code(device_code)


# ---------------- MANIFEST ----------------
@app.get("/manifest.json")
def manifest():
    return {
        "id": "org.seedrcc.stremio",
        "version": "1.0.0",
        "name": "Seedr.cc Personal Addon",
        "description": "Stream and browse your Seedr.cc files directly in Stremio",
        "resources": ["stream", "catalog", "meta"],
        "types": ["movie"],
        "catalogs": [
            {
                "type": "movie",
                "id": "seedr-movies",
                "name": "My Seedr Movies"
            }
        ]
    }


# ---------------- DEBUG ----------------
@app.get("/debug/files")
def debug_files():
    result = []
    with get_client() as client:
        contents = client.list_contents()
        for f in contents.files:
            result.append({
                "file_id": f.file_id,
                "folder_file_id": f.folder_file_id,
                "name": f.name,
                "size": f.size,
                "play_video": f.play_video,
                "thumb": f.thumb
            })
    return result


# ---------------- CATALOG ----------------
@app.get("/catalog/{type}/{id}.json")
def catalog(type: str, id: str):
    metas = []

    with get_client() as client:
        contents = client.list_contents()

        for f in contents.files:
            if f.play_video:
                metas.append({
                    "id": str(f.file_id),
                    "type": "movie",
                    "name": f.name,
                    "poster": f.thumb,
                    "description": f.name
                })

    return {"metas": metas}


# ---------------- META ----------------
@app.get("/meta/{type}/{id}.json")
def meta(type: str, id: str):
    with get_client() a_
