from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from typing import List
import json
import os

from app.database import init_db
from app.routers import (
    market_router, portfolio_router, watchlist_router,
    alerts_router, settings_router, analysis_router,
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="FinSight API", version="0.1.0", lifespan=lifespan)

_cors_origins = os.environ.get("CORS_ORIGINS", "https://finsight-28ky.onrender.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[s.strip() for s in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)
app.include_router(alerts_router)
app.include_router(settings_router)
app.include_router(analysis_router)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Serve built frontend in production
# __file__ = /app/app/main.py → go up two dirs to /app, then /static
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

if os.path.isdir(static_path):
    app.mount("/static", StaticFiles(directory=static_path, html=False), name="static")

    def read_index():
        idx = os.path.join(static_path, "index.html")
        if os.path.exists(idx):
            with open(idx) as f:
                return f.read()
        return None

    @app.get("/")
    async def serve_root():
        html = read_index()
        if html:
            return HTMLResponse(content=html)
        return {"detail": "Frontend not built"}

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        # Never intercept API paths
        if path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        # Serve static files with correct MIME type
        file_path = os.path.join(static_path, path)
        if os.path.isfile(file_path):
            from fastapi.responses import FileResponse
            return FileResponse(file_path)
        # Fall back to index.html for SPA routing
        html = read_index()
        if html:
            return HTMLResponse(content=html)
        return {"detail": "Not found"}


@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/ws/broadcast-alert")
async def broadcast_alert(ticker: str, message: str, secret: str = ""):
    if secret != os.environ.get("BROADCAST_SECRET", ""):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    await manager.broadcast({"type": "alert", "ticker": ticker, "message": message})
    return {"sent": True}
