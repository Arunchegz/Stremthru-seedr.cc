from fastapi import FastAPI, HTTPException
from seedr_client import get_client

app = FastAPI()


@app.get("/")
def root():
    return {"status": "alive"}


@app.get("/stream/{type}/{id}.json")
def stream(type: str, id: str):
    try:
        client = get_client()
    except Exception as e:
        return {"streams": [], "error": str(e)}

    contents = client.list_contents()

    video_exts = (".mp4", ".mkv", ".avi", ".mov", ".webm")
    video = None

    for f in contents.files:
        if f.name.lower().endswith(video_exts):
            video = f
            break

    if not video:
        return {"streams": []}

    link = client.fetch_file(video.folder_file_id)

    return {
        "streams": [
            {
                "name": "Seedr",
                "title": video.name,
                "url": link.url
            }
        ]
    }
