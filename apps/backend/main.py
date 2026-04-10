from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .state_store import load_state, save_state

app = FastAPI(title="matrix-codex-status")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients: list[WebSocket] = []
STATE: dict[str, Any] = load_state()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
def get_status() -> dict[str, Any]:
    return STATE


@app.post("/event")
async def event(data: dict[str, Any]) -> dict[str, bool]:
    repo = str(data.get("repo", "unknown"))
    status = str(data.get("status", "unknown"))

    enriched = {
        **data,
        "repo": repo,
        "status": status,
        "updated": time.time(),
    }

    STATE.setdefault("repos", {})[repo] = {"status": status, "updated": enriched["updated"]}
    STATE.setdefault("actions", []).append(enriched)
    STATE["actions"] = STATE["actions"][-500:]
    save_state(STATE)

    stale: list[WebSocket] = []
    for client in clients:
        try:
            await client.send_json(enriched)
        except Exception:
            stale.append(client)
    for client in stale:
        if client in clients:
            clients.remove(client)

    return {"ok": True}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if ws in clients:
            clients.remove(ws)
