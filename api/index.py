from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from seedrcc import AsyncSeedr # Using seedrcc (latest wrapper)
import uvicorn

app = FastAPI()

# --- STREMIO MANIFEST ---
def get_manifest(token: str = None):
    return {
        "id": "community.seedr.addon",
        "version": "1.0.0",
        "name": "Seedr Cloud Streamer",
        "description": "Stream your Seedr.cc files directly in Stremio",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "idPrefixes": ["tt"], # IMDb IDs
        "usageHint": "Add your token to the URL to access your files."
    }

@app.get("/{token}/manifest.json")
async def manifest(token: str):
    return get_manifest(token)

# --- STREAM HANDLER ---
@app.get("/{token}/stream/{type}/{id}.json")
async def stream_handler(token: str, type: str, id: str):
    """
    Logic: 
    1. Connect to Seedr using the token.
    2. Search your cloud for the IMDb ID (or file name matching).
    3. Return the direct stream link.
    """
    async with AsyncSeedr(token=token) as seedr:
        # Fetch all files in the root
        contents = await seedr.list_contents()
        streams = []

        # Simplified Search Logic:
        # In a real scenario, you'd fetch meta from TMDB/IMDb to get the title
        # For now, we search folders/files for the IMDb ID or common naming
        for folder in contents.get('folders', []):
            # If folder name contains part of the ID or you use a mapping service
            # Here we just list everything for demonstration:
            files = await seedr.list_contents(folder['id'])
            for f in files.get('files', []):
                if f['play_video']: # If it's a video file
                    # Fetch direct stream link
                    stream_data = await seedr.get_file(f['id'])
                    streams.append({
                        "name": "Seedr Cloud",
                        "title": f['name'],
                        "url": stream_data['url'] 
                    })

        return {"streams": streams}

# --- AUTH LOGIC (Your requested method) ---
@app.get("/get-device-code")
async def get_device_code():
    async with AsyncSeedr() as seedr:
        # This triggers the Seedr Device Flow
        device_code = await seedr.get_device_code()
        return device_code

@app.get("/authorize/{device_code}")
async def authorize(device_code: str):
    async with AsyncSeedr() as seedr:
        # Once the user enters the code on seedr.cc/devices
        response = await seedr.authorize(device_code)
        # We return the token for the user to put into Stremio
        return {"token": seedr.token, "install_url": f"stremio://YOUR_VERCEL_URL/{seedr.token}/manifest.json"}
