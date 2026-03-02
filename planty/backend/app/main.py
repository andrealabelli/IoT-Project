from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, devices, events
from app.models.database import Base, engine
from app.mqtt.client import mqtt_service
from app.services.realtime import manager

app = FastAPI(title="Planty API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(events.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    mqtt_service.start()


@app.get("/health")
def health():
    return {"ok": True}


@app.websocket("/ws/{device_id}")
async def ws_device(websocket: WebSocket, device_id: str):
    await manager.connect(device_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(device_id, websocket)
