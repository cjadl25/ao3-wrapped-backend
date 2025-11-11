# app_live.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import os
from scraper_live import scrape_ao3_with_progress

app = FastAPI(title="AO3 Wrapped Backend")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend_live"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join("frontend_live", "index_live.html"))

# In-memory store for scraping progress/results
scrape_progress = {
    "progress": 0,
    "done": False,
    "results": None,
    "error": None
}

@app.post("/api/start-scrape")
async def start_scrape(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    consent = data.get("consent")

    if not username or not password or not consent:
        raise HTTPException(status_code=400, detail="Username, password, and consent required")

    # Reset progress
    scrape_progress.update({"progress": 0, "done": False, "results": None, "error": None})

    # Start scraper in background
    asyncio.create_task(run_scraper_background(username, password))

    return {"status": "scrape_started"}

async def run_scraper_background(username, password):
    def progress_callback(progress_percentage):
        scrape_progress["progress"] = progress_percentage

    loop = asyncio.get_event_loop()
    try:
        results = await loop.run_in_executor(
            None, scrape_ao3_with_progress, username, password, progress_callback
        )
        scrape_progress.update({"progress": 100, "done": True, "results": results})
    except Exception as e:
        scrape_progress.update({"progress": 100, "done": True, "results": None, "error": str(e)})

@app.get("/api/scrape-progress")
async def get_progress():
    return scrape_progress

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
