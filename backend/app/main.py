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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Serve built frontend in production
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

    @app.get("/{path:path}", response_class=HTMLResponse)
    async def serve_spa(path: str):
        index_path = os.path.join(static_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                return f.read()
        return {"detail": "Frontend not built"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


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
async def broadcast_alert(ticker: str, message: str):
    await manager.broadcast({"type": "alert", "ticker": ticker, "message": message})
    return {"sent": True}
