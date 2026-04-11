from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from matrix_codex.api.routes import router as maintainer_router
from matrix_codex.settings import get_settings
from matrix_codex.storage.models import EventRecord, StorageDB

app = FastAPI(title="matrix-codex-status")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients: list[WebSocket] = []
settings = get_settings()
store = StorageDB(settings.state_dir / "maintainer_records.json")
STATE: dict[str, Any] = {"repos": {}, "actions": []}


@app.on_event("startup")
def load_persisted_state() -> None:
    for event in store.list("events")[-200:]:
        repo = str(event.get("repo", "unknown"))
        status = str(event.get("status", "unknown"))
        updated = time.time()
        STATE["repos"][repo] = {"status": status, "updated": updated}
        STATE["actions"].append({**event, "updated": updated})


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
    run_id = str(data.get("run_id", ""))

    enriched = {
        **data,
        "repo": repo,
        "status": status,
        "updated": time.time(),
    }

    STATE["repos"][repo] = {"status": status, "updated": enriched["updated"]}
    STATE["actions"].append(enriched)
    STATE["actions"] = STATE["actions"][-200:]

    from uuid import uuid4

    store.append(
        "events",
        EventRecord(
            event_id=str(uuid4()),
            run_id=run_id,
            repo=repo,
            status=status,
            payload=data,
        ),
    )

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


app.include_router(maintainer_router)
