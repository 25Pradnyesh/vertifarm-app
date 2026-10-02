import json
import pytest
from app.db.session import db
from app.models.domain import SensorReading
from app.services.mqtt_service import mqtt_service, evaluate_reading_status
from app.services.realtime_service import realtime_service

def test_mqtt_topic_parsing():
    parsed = mqtt_service.parse_topic("vertifarm/farm-1/s-1/telemetry")
    assert parsed["farm_id"] == "farm-1"
    assert parsed["sensor_id"] == "s-1"

    parsed_batch = mqtt_service.parse_topic("vertifarm/farm-2/telemetry")
    assert parsed_batch["farm_id"] == "farm-2"

def test_valid_single_telemetry_payload_ingestion():
    mqtt_service.dedup.clear()
    topic = "vertifarm/farm-1/s-1/telemetry"
    payload = json.dumps({
        "metric": "temperature",
        "value": 26.5,
        "unit": "°C",
        "timestamp": "2026-10-02T10:00:00Z"
    }).encode("utf-8")

    readings = mqtt_service.process_payload(topic, payload)
    assert len(readings) == 1
    reading = readings[0]
    assert reading.metric == "temperature"
    assert reading.value == 26.5
    assert reading.unit == "°C"
    assert reading.status == "healthy"
    assert reading.sensor_id == "s-1"
    assert reading.farm_id == "farm-1"

    # Verify persisted in database
    latest = db.get_latest_readings("farm-1")
    temp_latest = next((r for r in latest if r.metric == "temperature"), None)
    assert temp_latest is not None
    assert temp_latest.value == 26.5

def test_valid_batch_telemetry_payload_ingestion():
    mqtt_service.dedup.clear()
    topic = "vertifarm/farm-1/telemetry"
    payload = json.dumps({
        "farm_id": "farm-1",
        "readings": [
            {"sensor_id": "s-2", "metric": "humidity", "value": 68.0, "unit": "%"},
            {"sensor_id": "s-3", "metric": "soilMoisture", "value": 52.0, "unit": "%"}
        ]
    }).encode("utf-8")

    readings = mqtt_service.process_payload(topic, payload)
    assert len(readings) == 2
    metrics = {r.metric for r in readings}
    assert "humidity" in metrics
    assert "soilMoisture" in metrics

def test_metric_alias_normalization():
    mqtt_service.dedup.clear()
    assert mqtt_service.normalize_metric("temp") == "temperature"
    assert mqtt_service.normalize_metric("hum") == "humidity"
    assert mqtt_service.normalize_metric("soil_moisture") == "soilMoisture"
    assert mqtt_service.normalize_metric("lux") == "light"

    # Ingest using alias
    reading = mqtt_service.ingest_reading(
        sensor_id="s-alias",
        metric="soil_moisture",
        value=45.0,
        farm_id="farm-1",
    )
    assert reading is not None
    assert reading.metric == "soilMoisture"

def test_invalid_payload_json_rejection():
    # Malformed JSON must not crash
    topic = "vertifarm/farm-1/s-1/telemetry"
    readings = mqtt_service.process_payload(topic, b"not-a-valid-json-{{{")
    assert readings == []

def test_invalid_payload_binary_decode_rejection():
    # Non-UTF8 payload must not crash
    topic = "vertifarm/farm-1/s-1/telemetry"
    readings = mqtt_service.process_payload(topic, b"\x80\x81\x82\xff")
    assert readings == []

def test_missing_metric_or_value_rejection():
    mqtt_service.dedup.clear()
    # Missing value
    r1 = mqtt_service.ingest_reading(sensor_id="s-1", metric="temperature", value=None)
    assert r1 is None

    # Missing metric
    r2 = mqtt_service.ingest_reading(sensor_id="s-1", metric="", value=25.0)
    assert r2 is None

def test_unknown_metric_rejection():
    r = mqtt_service.ingest_reading(sensor_id="s-1", metric="unknown_vibe_metric", value=100.0)
    assert r is None

def test_non_numeric_and_nan_value_rejection():
    r1 = mqtt_service.ingest_reading(sensor_id="s-1", metric="temperature", value="invalid_number")
    assert r1 is None

    r2 = mqtt_service.ingest_reading(sensor_id="s-1", metric="temperature", value=float("nan"))
    assert r2 is None

    r3 = mqtt_service.ingest_reading(sensor_id="s-1", metric="temperature", value=float("inf"))
    assert r3 is None

def test_physical_bounds_validation():
    # pH must be within 0.0 to 14.0
    r_high = mqtt_service.ingest_reading(sensor_id="s-ph", metric="ph", value=16.8)
    assert r_high is None

    r_low = mqtt_service.ingest_reading(sensor_id="s-ph", metric="ph", value=-2.0)
    assert r_low is None

    r_valid = mqtt_service.ingest_reading(sensor_id="s-ph", metric="ph", value=6.5)
    assert r_valid is not None
    assert r_valid.value == 6.5

def test_duplicate_reading_deduplication():
    mqtt_service.dedup.clear()
    topic = "vertifarm/farm-1/s-1/telemetry"
    payload = json.dumps({
        "metric": "temperature",
        "value": 27.2,
        "timestamp": "2026-10-02T10:15:00Z"
    }).encode("utf-8")

    first_run = mqtt_service.process_payload(topic, payload)
    assert len(first_run) == 1

    # Sending exact same payload again should be deduplicated
    second_run = mqtt_service.process_payload(topic, payload)
    assert len(second_run) == 0

def test_agronomic_status_evaluation():
    status, label = evaluate_reading_status("temperature", 24.0)
    assert status == "healthy"

    status_warn, _ = evaluate_reading_status("temperature", 34.0)
    assert status_warn == "warning"

    status_crit, _ = evaluate_reading_status("temperature", 38.0)
    assert status_crit == "critical"

def test_telemetry_summary_updates_on_ingestion():
    mqtt_service.dedup.clear()
    reading = mqtt_service.ingest_reading(
        sensor_id="s-1",
        metric="temperature",
        value=28.4,
        farm_id="farm-1",
        timestamp="2026-10-02T11:00:00Z"
    )
    assert reading is not None

    summary = db.telemetry_summaries["farm-1"]["temperature"]
    assert summary.current_value == 28.4
    assert 28.4 in summary.trend
    # Sensor status updated
    assert db.sensors["s-1"].status == "active"

def test_realtime_service_broadcast():
    queue = realtime_service.register()
    try:
        sample_reading = SensorReading(
            id="read-test-rt",
            sensor_id="s-rt",
            farm_id="farm-1",
            metric="light",
            value=1450.0,
            unit="Lux",
            status="healthy",
            status_label="Optimal",
        )
        realtime_service.broadcast_reading_sync(sample_reading)
        assert not queue.empty()
        msg = queue.get_nowait()
        assert msg["type"] == "telemetry_reading"
        assert msg["data"]["metric"] == "light"
        assert msg["data"]["value"] == 1450.0
    finally:
        realtime_service.unregister(queue)

def test_api_latest_telemetry_readings(client, auth_headers):
    response = client.get("/api/v1/telemetry/latest", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "metric" in first
    assert "value" in first
    assert "sensorId" in first

def test_api_readings_history(client, auth_headers):
    response = client.get("/api/v1/telemetry/readings?limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_api_telemetry_http_ingest_valid(client, auth_headers):
    mqtt_service.dedup.clear()
    payload = {
        "sensorId": "s-http-1",
        "metric": "tds",
        "value": 640.0,
        "unit": "ppm",
        "farmId": "farm-1",
    }
    response = client.post("/api/v1/telemetry/ingest", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["metric"] == "tds"
    assert data["value"] == 640.0
    assert data["status"] == "healthy"

def test_api_telemetry_http_ingest_invalid(client, auth_headers):
    payload = {
        "sensorId": "s-bad",
        "metric": "invalid_metric",
        "value": 999.0,
    }
    response = client.post("/api/v1/telemetry/ingest", json=payload, headers=auth_headers)
    assert response.status_code == 422
