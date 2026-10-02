import asyncio
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.telemetry import (
    TelemetrySummary,
    FarmHealthStatus,
    SensorReadingSchema,
    TelemetryIngestPayload,
)
from app.services.telemetry_service import telemetry_service
from app.services.realtime_service import realtime_service

router = APIRouter()

@router.get("/summary", response_model=List[TelemetrySummary])
def get_telemetry_summaries(
    farm_id: Optional[str] = Query(None, alias="farmId"),
    user: User = Depends(get_current_user),
):
    """
    Fetches latest 24-hour summary across all 6 environmental metrics.
    """
    return telemetry_service.get_telemetry_summaries(user.id, farm_id)

@router.get("/health", response_model=FarmHealthStatus)
def get_farm_health(
    farm_id: Optional[str] = Query(None, alias="farmId"),
    user: User = Depends(get_current_user),
):
    """
    Evaluates telemetry metrics to report overall farm health.
    """
    return telemetry_service.get_farm_health_status(user.id, farm_id)

@router.get("/latest", response_model=List[SensorReadingSchema])
def get_latest_readings(
    farm_id: Optional[str] = Query(None, alias="farmId"),
    user: User = Depends(get_current_user),
):
    """
    Fetches the latest real-time reading for each environmental metric.
    """
    return telemetry_service.get_latest_readings(user.id, farm_id)

@router.get("/readings", response_model=List[SensorReadingSchema])
def get_readings_history(
    farm_id: Optional[str] = Query(None, alias="farmId"),
    metric: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
):
    """
    Fetches raw historical telemetry readings.
    """
    return telemetry_service.get_readings_history(user.id, farm_id, metric, limit)

@router.post("/ingest", response_model=SensorReadingSchema, status_code=status.HTTP_201_CREATED)
def ingest_telemetry_reading(
    payload: TelemetryIngestPayload,
):
    """
    HTTP endpoint for edge devices or gateways to submit telemetry readings.
    Shares the same validation, deduplication, and persistence logic as MQTT.
    """
    reading = telemetry_service.ingest_reading(payload)
    if not reading:
        raise HTTPException(
            status_code=422,
            detail="Telemetry payload rejected: invalid metric, out-of-bounds value, or duplicate reading.",
        )
    return reading


@router.websocket("/ws")
async def telemetry_websocket(websocket: WebSocket):
    """
    Realtime WebSocket stream for push-based telemetry updates to client apps.
    Broadcasts live readings immediately upon ingestion.
    """
    await websocket.accept()
    queue = realtime_service.register()
    try:
        await websocket.send_json({
            "type": "connection_established",
            "status": "connected",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

        async def client_listener():
            try:
                while True:
                    await websocket.receive_text()
            except Exception:
                pass

        listener_task = asyncio.create_task(client_listener())
        try:
            while not listener_task.done():
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                    await websocket.send_json(msg)
                except asyncio.TimeoutError:
                    continue
        finally:
            listener_task.cancel()
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        realtime_service.unregister(queue)

@router.get("/{metric}", response_model=TelemetrySummary)
def get_telemetry_by_metric(
    metric: str,
    range: str = Query("24H"),
    farm_id: Optional[str] = Query(None, alias="farmId"),
    user: User = Depends(get_current_user),
):
    """
    Fetches time-series trend points and stats for a specific metric.
    """
    summary = telemetry_service.get_telemetry_by_metric(metric, user.id, farm_id, range)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry metric '{metric}' not found.",
        )
    return summary
