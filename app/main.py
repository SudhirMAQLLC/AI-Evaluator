from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import asyncio
import logging

# Minimal FastAPI app for production
app = FastAPI(
    title="Assignment Evaluator",
    description="Automated evaluation system for technical assignments",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if present
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up logger for streaming
logger = logging.getLogger("uvicorn.error")
log_queue = asyncio.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        asyncio.create_task(log_queue.put(log_entry))

# Add handler if not already present
if not any(isinstance(h, QueueHandler) for h in logger.handlers):
    handler = QueueHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)

@app.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            log_entry = await log_queue.get()
            await websocket.send_text(log_entry)
    except WebSocketDisconnect:
        pass

@app.get("/")
async def root():
    return {
        "message": "Assignment Evaluator API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 