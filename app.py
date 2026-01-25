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


# Create Seedr client using device code from Railway variable
def get_client():
    device_code = os.environ["SEEDR_DEVICE_CODE"]
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


# Debug endpoint to see what Railway actually sees in your Seedr account
@app.get("/debug/files")
def debug_files():
    result = []
    with get_client() as client:
        contents = client.list_contents()
        for f in contents.files:
            result.append({
                "file_id": f.file_id,
                "name": f.name,
                "size": f.size,
                "play_video": f.play_video
            })
    return result


@app.get("/stream/{type}/{id}.json")
def stream(type: str, id: str):
    streams = []

    try:
        with get_client() as client:
            contents = client.list_contents()

            for file in contents.files:
                if str(file.file_id) == str(id) and file.play_video:
                    # Seedr stores the real streaming URL in raw metadata
                    raw = file.get_raw()

                    url = (
                        raw.get("download_url")
                        or raw.get("url")
                        or raw.get("stream_url")
                    )

                    if not url:
                        continue

                    streams.append({
                        "name": file.name,
                        "title": file.name,
                        "url": url,
                        "behaviorHints": {
                            "notWebReady": False
                        }
                    })

    except Exception as e:
        # Never crash Stremio; always return valid JSON
        return {
            "streams": [],
            "error": str(e)
        }

    return {"streams": streams}
