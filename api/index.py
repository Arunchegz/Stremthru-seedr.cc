from fastapi import FastAPI
from fastapi.responses import JSONResponse
from aioseedrcc import Login, Seedr
import asyncio

app = FastAPI()

# 1. ROOT ROUTE (To test if Vercel is working)
@app.get("/")
async def root():
    return {"status": "Seedr Addon is Online", "usage": "Go to /get-device-code to start"}

# 2. DEVICE CODE FLOW
@app.get("/get-device-code")
async def get_device_code():
    async with Login() as seedr_login:
        code = await seedr_login.get_device_code()
        return code

# 3. STREMIO MANIFEST
@app.get("/{token}/manifest.json")
async def manifest(token: str):
    return {
        "id": "com.seedr.stremio",
        "version": "1.0.0",
        "name": "Seedr Streamer",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "idPrefixes": ["tt"]
    }

# 4. STREAM RESOLVER (Production Logic)
@app.get("/{token}/stream/{type}/{id}.json")
async def stream_provider(token: str, type: str, id: str):
    async with Seedr(token=token) as seedr:
        # Get all files in Seedr
        files = await seedr.list_contents()
        streams = []
        
        # We look for files. In production, you'd match IMDb ID names.
        # This searches for video files in your folders
        for folder in files.get('folders', []):
            inner = await seedr.list_contents(folder['id'])
            for f in inner.get('files', []):
                if f.get('play_video'):
                    # Get the direct stream link
                    link_data = await seedr.get_file(f['id'])
                    streams.append({
                        "name": "Seedr",
                        "title": f['name'],
                        "url": link_data['url']
                    })
        
        return {"streams": streams}
        
