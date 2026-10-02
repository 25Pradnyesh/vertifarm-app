import asyncio
import json
import logging
from typing import Set, Dict, Any, Optional
from app.models.domain import SensorReading

logger = logging.getLogger("vertifarm.realtime")

class RealtimeService:
    """
    Realtime telemetry update broadcaster.
    Maintains active client subscriber queues (e.g., WebSockets, SSE)
    and provides a clean interface for Supabase Realtime / PostgreSQL CDC replication.
    """
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def register(self) -> asyncio.Queue:
        """Register a new client subscriber queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        logger.debug(f"New realtime subscriber registered. Total: {len(self._subscribers)}")
        return queue

    def unregister(self, queue: asyncio.Queue):
        """Remove a client subscriber queue."""
        self._subscribers.discard(queue)
        logger.debug(f"Realtime subscriber unregistered. Remaining: {len(self._subscribers)}")

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        """Asynchronously broadcast an event to all connected subscriber queues."""
        if not self._subscribers:
            return

        message = {
            "type": event_type,
            "data": payload,
        }

        dead_queues = set()
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # Remove stale / unresponsive queue
                dead_queues.add(queue)
            except Exception as e:
                logger.warning(f"Error delivering realtime broadcast to subscriber: {e}")
                dead_queues.add(queue)

        for dq in dead_queues:
            self._subscribers.discard(dq)

    async def broadcast_reading(self, reading: SensorReading):
        """Broadcast a new telemetry reading event."""
        payload = {
            "id": reading.id,
            "sensorId": reading.sensor_id,
            "farmId": reading.farm_id,
            "metric": reading.metric,
            "value": reading.value,
            "unit": reading.unit,
            "status": reading.status,
            "statusLabel": reading.status_label,
            "timestamp": reading.timestamp,
        }
        await self.broadcast("telemetry_reading", payload)

    def broadcast_sync(self, event_type: str, payload: Dict[str, Any]):
        """
        Thread-safe synchronous broadcast dispatch.
        Can be called from synchronous threads (e.g., Paho-MQTT client thread).
        """
        try:
            loop = self._loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(event_type, payload), loop)
            else:
                # Direct queue append if loop isn't running or in test mode
                for queue in list(self._subscribers):
                    try:
                        queue.put_nowait({"type": event_type, "data": payload})
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Sync broadcast dispatch skipped: {e}")

    def broadcast_reading_sync(self, reading: SensorReading):
        """Synchronously broadcast a sensor reading from non-async contexts."""
        payload = {
            "id": reading.id,
            "sensorId": reading.sensor_id,
            "farmId": reading.farm_id,
            "metric": reading.metric,
            "value": reading.value,
            "unit": reading.unit,
            "status": reading.status,
            "statusLabel": reading.status_label,
            "timestamp": reading.timestamp,
        }
        self.broadcast_sync("telemetry_reading", payload)

# Global Realtime singleton
realtime_service = RealtimeService()
