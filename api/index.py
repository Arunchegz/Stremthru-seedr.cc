from fastapi import FastAPI
from fastapi.responses import JSONResponse
from seedrcc import AsyncSeedr # Using seedrcc for better stability
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Online", "message": "Seedr Stremio Addon"}

@app.get("/get-device-code")
async def get_device_code():
    try:
        async with AsyncSeedr() as seedr:
            code = await seedr.get_device_code()
            return code
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/{token}/manifest.json")
async def manifest(token: str):
    return {
        "id": "community.seedr.addon",
        "version": "1.0.0",
        "name": "Seedr Cloud",
        "resources": ["stream"],
        "types": ["movie", "series"],
        "idPrefixes": ["tt"]
    }

@app.get("/{token}/stream/{type}/{id}.json")
async def stream_handler(token: str, type: str, id: str):
    try:
        async with AsyncSeedr(token=token) as seedr:
            contents = await seedr.list_contents()
            streams = []
            
            # Simple recursive search for video files
            for folder in contents.get('folders', []):
                files = await seedr.list_contents(folder['id'])
                for f in files.get('files', []):
                    if f.get('play_video'):
                        file_details = await seedr.get_file(f['id'])
                        streams.append({
                            "name": "Seedr",
                            "title": f['name'],
                            "url": file_details['url']
                        })
            return {"streams": streams}
    except Exception as e:
        return {"streams": [], "error": str(e)}

# Critical for Vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
