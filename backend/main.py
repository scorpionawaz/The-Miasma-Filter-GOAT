# server.py (or the file you posted at top)
import datetime
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from checker import AudioLoop
import base64
import asyncio
import uvicorn
from notifications import notifier
from fastapi import FastAPI ,Request
from fastapi.responses import JSONResponse
import json
import os
from infopool import infogather
from infopool import googlenews, googlenewslocation,    youtubelivecheck, youtubelivechecklocation
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] for all origins (less secure)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.on_event("startup")
async def start_background_tasks():
    print("Starting hourly background data generation...")

    async def periodic_data_generation():
        while True:
            try:
                print(f"[{datetime.datetime.now()}] Running infogather.generate('Delhi')")
                await asyncio.to_thread(infogather.generate, "Delhi")
            except Exception as e:
                print(f"Error during infogather.generate: {e}")
            await asyncio.sleep(3600)  # Wait 1 hour before next run

    asyncio.create_task(periodic_data_generation())




# this route is created by shriniwas and is used to render the trending topic on main page
@app.get("/globaltrends")
async def get_google_global_news():
    # Optionally read location, but not needed for global news
    googleglobalnews = googlenews.get_google_news_json()
    if isinstance(googleglobalnews, str):
        googleglobalnews = json.loads(googleglobalnews)

    # Do minutes_since fix if you use it elsewhere
    def sanitize_minutes_since(items):
        sanitized = []
        for item in items:
            if isinstance(item, dict):
                ms = item.get("minutes_since")
                if ms is None or ms == float('inf') or ms == "Infinity":
                    item["minutes_since"] = None
                sanitized.append(item)
        return sanitized

    googleglobalnews = sanitize_minutes_since(googleglobalnews)

    # Return only global news list
    return JSONResponse(content={"global": googleglobalnews})


@app.post("/trends")
async def get_trends(request: Request):
    body = await request.json()
    print("Received request body:", body)
    location = body.get("location", "Delhi")  # fallback if not provided
    
    googleglobalnews = googlenews.get_google_news_json()
    if isinstance(googleglobalnews, str):
        googleglobalnews = json.loads(googleglobalnews)

    googlenewslocal = googlenewslocation.get_google_news_json_location(location)
    if isinstance(googlenewslocal, str):
        googlenewslocal = json.loads(googlenewslocal)
 
    youtubeglobalnews = youtubelivecheck.extract_youtube_live_streams()
    youtubelocalnews = youtubelivechecklocation.extract_youtube_live_streams_location(location)
    
    file_path = os.path.join(os.path.dirname(__file__), "cache.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
    except FileNotFoundError:
        cache_data = {"error": "cache.json not found"}
    except json.JSONDecodeError:
        cache_data = {"error": "Invalid JSON format in cache.json"}

    def sanitize_minutes_since(items):
        sanitized = []
        for item in items:
            if isinstance(item, dict):
                ms = item.get("minutes_since")
                if ms is None or ms == float('inf') or ms == "Infinity":
                    item["minutes_since"] = None
                sanitized.append(item)
        return sanitized

    googleglobalnews = sanitize_minutes_since(googleglobalnews)
    googlenewslocal = sanitize_minutes_since(googlenewslocal)

    response = {
        "location": location,
        "google_news": {
            "global": googleglobalnews,
            "local": googlenewslocal
        },
        "youtube_trends": {
            "global": youtubeglobalnews,
            "local": youtubelocalnews
        },
        "cache_data": cache_data
    }
    return JSONResponse(content=response)





@app.get("/cache")
async def get_cache():
    file_path = os.path.join(os.path.dirname(__file__), "cache.json")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except FileNotFoundError:
        return JSONResponse(content={"error": "cache.json not found"}, status_code=404)
    except json.JSONDecodeError:
        return JSONResponse(content={"error": "Invalid JSON format in cache.json"}, status_code=500)

@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    session_id = str(uuid.uuid4())
    await websocket.accept()
    
    # Simple notification sender
    notifier.set_websocket(websocket)
    
    # Create AudioLoop and set up notifications
    audio_loop = AudioLoop()
    audio_loop.set_session_id(session_id)
    
    # Send welcome notification (fire-and-forget so it doesn't block)
    asyncio.create_task(notifier.send("Session Started", f"Miasma session {session_id[:8]} started", "success"))
    
    audio_loop.start()
    
    async def receive_from_client():
        try:
            while True:
                data = await websocket.receive_json()
                media_type = data.get("type")
                if media_type == "audio":
                    audio_data = base64.b64decode(data['data'])
                    await audio_loop.media_in_queue.put({"data": audio_data, "mime_type": "audio/pcm"})
                elif media_type == "video":
                    image_data = data['data']
                    await audio_loop.media_in_queue.put({"mime_type": "image/jpeg", "data": base64.b64decode(image_data)})
        except WebSocketDisconnect:
            print("Client disconnected (receive task).")

    async def send_to_client():
        try:
            while True:
                message = await audio_loop.browser_out_queue.get()
                await websocket.send_json(message)
        except WebSocketDisconnect:
            print("Client disconnected (send task).")

    # Run tasks
    receive_task = asyncio.create_task(receive_from_client())
    send_task = asyncio.create_task(send_to_client())

    done, pending = await asyncio.wait(
        [receive_task, send_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
    audio_loop.stop()
    print(f"WebSocket connection for session {session_id} closed.")

if __name__ == "__main__":
    print("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
