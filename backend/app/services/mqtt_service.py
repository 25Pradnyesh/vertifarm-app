import collections
import json
import logging
import math
import time
import uuid
from typing import Optional, List, Dict, Any, Tuple
from app.core.config import settings
from app.db.session import db
from app.models.domain import SensorReading
from app.services.realtime_service import realtime_service

logger = logging.getLogger("vertifarm.mqtt")

METRIC_ALIASES: Dict[str, str] = {
    "temperature": "temperature",
    "temp": "temperature",
    "humidity": "humidity",
    "hum": "humidity",
    "soilmoisture": "soilMoisture",
    "soil_moisture": "soilMoisture",
    "moisture": "soilMoisture",
    "ph": "ph",
    "tds": "tds",
    "light": "light",
    "lux": "light",
}

VALID_METRICS = {"temperature", "humidity", "soilMoisture", "ph", "tds", "light"}

PHYSICAL_LIMITS: Dict[str, Tuple[float, float, str]] = {
    "temperature": (-40.0, 100.0, "°C"),
    "humidity": (0.0, 100.0, "%"),
    "soilMoisture": (0.0, 100.0, "%"),
    "ph": (0.0, 14.0, "pH"),
    "tds": (0.0, 5000.0, "ppm"),
    "light": (0.0, 150000.0, "Lux"),
}

def evaluate_reading_status(metric: str, value: float) -> Tuple[str, str]:
    """
    Evaluates metric reading against agronomic thresholds.
    Returns (status, status_label) where status is 'healthy' | 'warning' | 'critical'.
    """
    if metric == "temperature":
        if 20.0 <= value <= 30.0:
            return "healthy", "Normal"
        elif 15.0 <= value <= 35.0:
            return "warning", "Temperature Warning"
        return "critical", "Temperature Critical"

    if metric == "humidity":
        if 60.0 <= value <= 80.0:
            return "healthy", "Normal"
        elif 40.0 <= value <= 90.0:
            return "warning", "Humidity Warning"
        return "critical", "Humidity Critical"

    if metric == "soilMoisture":
        if 40.0 <= value <= 60.0:
            return "healthy", "Normal"
        elif 30.0 <= value <= 75.0:
            return "warning", "Moisture Warning"
        return "critical", "Moisture Critical"

    if metric == "ph":
        if 6.0 <= value <= 7.0:
            return "healthy", "Slightly Acidic" if value < 6.8 else "Normal"
        elif 5.5 <= value <= 7.5:
            return "warning", "pH Warning"
        return "critical", "pH Critical"

    if metric == "tds":
        if 500.0 <= value <= 800.0:
            return "healthy", "Normal"
        elif 400.0 <= value <= 1000.0:
            return "warning", "TDS Warning"
        return "critical", "TDS Critical"

    if metric == "light":
        if 1000.0 <= value <= 2000.0:
            return "healthy", "Optimal"
        elif 500.0 <= value <= 3000.0:
            return "warning", "Suboptimal Light"
        return "critical", "Light Warning"

    return "healthy", "Normal"

class DeduplicationCache:
    """Bounded sliding window cache to prevent duplicate processing of QoS 1 MQTT retransmissions."""
    def __init__(self, maxsize: int = 2000):
        self._maxsize = maxsize
        self._seen: set = set()
        self._queue: collections.deque = collections.deque()

    def is_duplicate(self, key: Tuple) -> bool:
        if key in self._seen:
            return True
        self._seen.add(key)
        self._queue.append(key)
        if len(self._queue) > self._maxsize:
            oldest = self._queue.popleft()
            self._seen.discard(oldest)
        return False

    def clear(self):
        self._seen.clear()
        self._queue.clear()

class MQTTService:
    """
    MQTT Ingestion Service for VertiFarm.
    Handles connection, subscription, payload parsing, metric validation,
    deduplication, database persistence, and realtime broadcasts.
    """
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.dedup = DeduplicationCache()

    def normalize_metric(self, raw_metric: str) -> Optional[str]:
        """Maps incoming metric aliases to canonical metric name."""
        if not raw_metric:
            return None
        cleaned = raw_metric.strip().lower()
        return METRIC_ALIASES.get(cleaned)

    def parse_topic(self, topic: str) -> Dict[str, Optional[str]]:
        """
        Parses topic conforming to:
        - vertifarm/{farm_id}/{sensor_id}/telemetry
        - vertifarm/{farm_id}/telemetry
        - vertifarm/{farm_id}/{zone_id}/telemetry
        """
        parts = topic.strip("/").split("/")
        info = {
            "prefix": parts[0] if len(parts) > 0 else None,
            "farm_id": None,
            "sensor_id": None,
            "zone_id": None,
        }
        if len(parts) >= 4 and parts[-1] == "telemetry":
            info["farm_id"] = parts[1]
            info["sensor_id"] = parts[2]
        elif len(parts) == 3 and parts[-1] == "telemetry":
            info["farm_id"] = parts[1]
        elif len(parts) == 2:
            info["farm_id"] = parts[1]
        return info

    def ingest_reading(
        self,
        sensor_id: str,
        metric: str,
        value: Any,
        unit: Optional[str] = None,
        farm_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> Optional[SensorReading]:
        """
        Validates and ingests a single reading.
        Returns the recorded SensorReading, or None if rejected.
        """
        # 1. Validate metric
        canonical_metric = self.normalize_metric(metric)
        if not canonical_metric or canonical_metric not in VALID_METRICS:
            logger.warning(f"Rejected telemetry: Unknown or unsupported metric '{metric}'")
            return None

        # 2. Validate value is numeric and finite
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            try:
                numeric_val = float(value)
            except (ValueError, TypeError):
                logger.warning(f"Rejected telemetry: Non-numeric value '{value}' for {canonical_metric}")
                return None
        else:
            numeric_val = float(value)

        if not math.isfinite(numeric_val):
            logger.warning(f"Rejected telemetry: Non-finite value '{value}' for {canonical_metric}")
            return None

        # 3. Validate physical bounds
        min_bound, max_bound, default_unit = PHYSICAL_LIMITS[canonical_metric]
        if not (min_bound <= numeric_val <= max_bound):
            logger.warning(
                f"Rejected telemetry: Value {numeric_val} outside physical bounds [{min_bound}, {max_bound}] for {canonical_metric}"
            )
            return None

        # 4. Resolve farm and sensor identification
        resolved_farm = farm_id or "farm-1"
        resolved_sensor = sensor_id or f"s-{canonical_metric}"
        resolved_unit = unit or default_unit
        resolved_timestamp = timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 5. Check deduplication
        dedup_key = (
            resolved_farm,
            resolved_sensor,
            canonical_metric,
            round(numeric_val, 2),
            resolved_timestamp,
        )
        if self.dedup.is_duplicate(dedup_key):
            logger.debug(f"Deduplicated reading for {resolved_sensor} - {canonical_metric}")
            return None

        # 6. Evaluate agronomic status
        status, status_label = evaluate_reading_status(canonical_metric, numeric_val)

        # 7. Construct domain model
        reading = SensorReading(
            id=f"read-{uuid.uuid4().hex[:12]}",
            sensor_id=resolved_sensor,
            farm_id=resolved_farm,
            metric=canonical_metric,
            value=round(numeric_val, 2),
            unit=resolved_unit,
            status=status,
            status_label=status_label,
            timestamp=resolved_timestamp,
            zone_id=zone_id,
        )

        # 8. Persist to database
        db.record_reading(reading)

        # 9. Realtime broadcast
        realtime_service.broadcast_reading_sync(reading)

        logger.info(
            f"Successfully ingested telemetry: farm={resolved_farm} sensor={resolved_sensor} "
            f"metric={canonical_metric} value={reading.value}{reading.unit} status={reading.status}"
        )
        return reading

    def process_payload(self, topic: str, payload_bytes: bytes) -> List[SensorReading]:
        """
        Parses topic and payload safely.
        Supports single reading payloads as well as batch reading payloads.
        Returns a list of successfully ingested SensorReading instances.
        """
        # Decode UTF-8 safely
        try:
            payload_str = payload_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.warning(f"MQTT payload UTF-8 decode error: {e}")
            return []

        # Parse JSON safely
        try:
            data = json.loads(payload_str)
        except json.JSONDecodeError as e:
            logger.warning(f"MQTT payload JSON parse error: {e}. Raw: {payload_str[:100]}")
            return []

        topic_info = self.parse_topic(topic)
        ingested: List[SensorReading] = []

        if isinstance(data, list):
            # Array of readings
            for item in data:
                if isinstance(item, dict):
                    reading = self._process_dict_item(item, topic_info)
                    if reading:
                        ingested.append(reading)
        elif isinstance(data, dict):
            if "readings" in data and isinstance(data["readings"], list):
                # Batch envelope
                batch_farm = data.get("farm_id") or data.get("farmId") or topic_info["farm_id"]
                batch_zone = data.get("zone_id") or data.get("zoneId") or topic_info["zone_id"]
                for item in data["readings"]:
                    if isinstance(item, dict):
                        item_farm = item.get("farm_id") or item.get("farmId") or batch_farm
                        item_zone = item.get("zone_id") or item.get("zoneId") or batch_zone
                        reading = self._process_dict_item(item, {
                            "farm_id": item_farm,
                            "sensor_id": item.get("sensor_id") or item.get("sensorId") or topic_info["sensor_id"],
                            "zone_id": item_zone,
                        })
                        if reading:
                            ingested.append(reading)
            else:
                # Single reading dictionary
                reading = self._process_dict_item(data, topic_info)
                if reading:
                    ingested.append(reading)
        else:
            logger.warning(f"Invalid MQTT payload structure: expected dict or list, got {type(data)}")

        return ingested

    def _process_dict_item(self, item: Dict[str, Any], topic_info: Dict[str, Optional[str]]) -> Optional[SensorReading]:
        """Extracts fields and delegates to ingest_reading."""
        sensor_id = (
            item.get("sensor_id")
            or item.get("sensorId")
            or item.get("sensor")
            or topic_info.get("sensor_id")
        )
        metric = item.get("metric") or item.get("type")
        value = item.get("value")
        unit = item.get("unit")
        farm_id = (
            item.get("farm_id")
            or item.get("farmId")
            or topic_info.get("farm_id")
        )
        zone_id = (
            item.get("zone_id")
            or item.get("zoneId")
            or topic_info.get("zone_id")
        )
        timestamp = item.get("timestamp") or item.get("time")

        if not metric or value is None:
            logger.warning(f"Telemetry item missing required 'metric' or 'value': {item}")
            return None

        return self.ingest_reading(
            sensor_id=sensor_id or "s-generic",
            metric=metric,
            value=value,
            unit=unit,
            farm_id=farm_id,
            zone_id=zone_id,
            timestamp=timestamp,
        )

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Callback triggered on successful broker connection."""
        if reason_code == 0 or getattr(reason_code, "value", reason_code) == 0:
            self.is_connected = True
            logger.info("Connected to MQTT broker successfully.")
            # Subscribe to telemetry topics
            topic = f"{settings.MQTT_TOPIC_PREFIX}/#"
            client.subscribe(topic, qos=1)
            logger.info(f"Subscribed to MQTT telemetry topic: {topic}")
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker, reason_code={reason_code}")

    def on_message(self, client, userdata, msg):
        """Callback triggered when an incoming MQTT message is received."""
        try:
            self.process_payload(msg.topic, msg.payload)
        except Exception as e:
            logger.error(f"Unhandled error in MQTT message handler: {e}", exc_info=True)

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code=None, properties=None):
        """Callback triggered on broker disconnection."""
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT broker, reason_code={reason_code}")

    def start(self):
        """Initializes and starts the MQTT client if MQTT_ENABLED is configured."""
        if not settings.MQTT_ENABLED:
            logger.info("MQTT is disabled (MQTT_ENABLED=false). Background client will not start.")
            return

        try:
            import paho.mqtt.client as mqtt

            # Create Paho client with CallbackAPIVersion.VERSION2
            if hasattr(mqtt, "CallbackAPIVersion"):
                self.client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION2,
                    client_id=settings.MQTT_CLIENT_ID,
                )
            else:
                self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)

            if settings.MQTT_USERNAME:
                self.client.username_pw_set(
                    username=settings.MQTT_USERNAME,
                    password=settings.MQTT_PASSWORD or None,
                )

            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect

            logger.info(
                f"Connecting to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}..."
            )
            self.client.connect(
                host=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
                keepalive=settings.MQTT_KEEPALIVE,
            )
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            self.is_connected = False

    def stop(self):
        """Stops the MQTT client background loop and disconnects."""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("MQTT client stopped.")
            except Exception as e:
                logger.warning(f"Error stopping MQTT client: {e}")
            finally:
                self.is_connected = False
                self.client = None

# Global MQTT Service singleton
mqtt_service = MQTTService()
