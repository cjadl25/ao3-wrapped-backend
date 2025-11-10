from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from scraper_live import scrape_ao3_with_progress
import asyncio
import os

app = FastAPI()

# Serve frontend folder
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join("frontend", "index_live.html"))

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your GitHub Pages URL for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory progress storage
scrape_progress = {"progress": 0, "done": False, "results": None}

@app.post("/api/start-scrape")
async def start_scrape(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    consent = data.get("consent")

    if not username or not password or not consent:
        raise HTTPException(status_code=400, detail="Username, password, and consent required")

    # Reset progress
    scrape_progress.update({"progress": 0, "done": False, "results": None})

    # Run scraper in background
    asyncio.create_task(run_scraper_background(username, password))
    return {"status": "scrape_started"}

async def run_scraper_background(username, password):
    def progress_callback(progress_percentage):
        scrape_progress["progress"] = progress_percentage

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, scrape_ao3_with_progress, username, password, progress_callback)
    scrape_progress.update({"progress": 100, "done": True, "results": results})

@app.get("/api/scrape-progress")
async def get_progress():
    return scrape_progress

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
