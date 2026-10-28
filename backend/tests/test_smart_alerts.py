import pytest
from app.db.session import db
from app.models.domain import SensorReading
from app.core.thresholds import evaluate_reading_threshold, SENSOR_THRESHOLDS
from app.services.alert_service import alert_service
from app.services.mqtt_service import mqtt_service

@pytest.fixture(autouse=True)
def clean_test_state():
    """Ensure clean alert state before each test."""
    db.alerts.clear()
    alert_service._active_directions.clear()
    mqtt_service.dedup.clear()

def test_readings_within_normal_ranges():
    """Readings in normal agronomic ranges must not trigger alerts."""
    normal_readings = [
        ("temperature", 24.5, "°C"),
        ("humidity", 68.0, "%"),
        ("soilMoisture", 50.0, "%"),
        ("ph", 6.5, "pH"),
        ("tds", 650.0, "ppm"),
        ("light", 1500.0, "Lux"),
    ]

    for metric, val, unit in normal_readings:
        reading = SensorReading(
            id=f"r-normal-{metric}",
            sensor_id=f"s-{metric}",
            farm_id="farm-test",
            metric=metric,
            value=val,
            unit=unit,
        )
        alert = alert_service.process_reading_telemetry(reading)
        assert alert is None
        assert len([a for a in db.alerts.values() if a.farm_id == "farm-test"]) == 0

def test_high_temperature_alert_generation():
    """High temperature must generate a correctly formatted alert."""
    reading = SensorReading(
        id="r-temp-high",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=34.0,
        unit="°C",
    )
    alert = alert_service.process_reading_telemetry(reading)
    assert alert is not None
    assert alert.metric == "temperature"
    assert alert.severity == "warning"
    assert "High temperature detected" in alert.description
    assert "34.0 °C" in alert.current_value
    assert "> 30.0 °C" in alert.threshold_value
    assert not alert.is_resolved

def test_critical_high_temperature_alert_generation():
    """Critical temperature (>35°C) must have critical severity."""
    reading = SensorReading(
        id="r-temp-crit",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=38.5,
        unit="°C",
    )
    alert = alert_service.process_reading_telemetry(reading)
    assert alert is not None
    assert alert.severity == "critical"
    assert alert.metric == "temperature"

def test_low_humidity_alert_generation():
    """Low humidity (<60% warning, <40% critical) must trigger alert."""
    reading_warn = SensorReading(
        id="r-hum-warn",
        sensor_id="s-hum",
        farm_id="farm-test",
        metric="humidity",
        value=48.0,
        unit="%",
    )
    alert = alert_service.process_reading_telemetry(reading_warn)
    assert alert is not None
    assert alert.metric == "humidity"
    assert alert.severity == "warning"
    assert "Humidity too low: 48.0 % — Minimum: 60.0 %" in alert.description

def test_critical_low_soil_moisture_alert():
    """Critical low soil moisture (<30%) must trigger critical alert."""
    reading = SensorReading(
        id="r-soil-crit",
        sensor_id="s-soil",
        farm_id="farm-test",
        metric="soilMoisture",
        value=22.0,
        unit="%",
    )
    alert = alert_service.process_reading_telemetry(reading)
    assert alert is not None
    assert alert.metric == "soilMoisture"
    assert alert.severity == "critical"
    assert "Soil Moisture critical: 22.0 % — Minimum: 40.0 %" in alert.description

def test_excessive_light_intensity_alert():
    """Excessive light intensity (>2000 Lux warning, >3000 Lux critical) must trigger alert."""
    reading = SensorReading(
        id="r-light-high",
        sensor_id="s-light",
        farm_id="farm-test",
        metric="light",
        value=3500.0,
        unit="Lux",
    )
    alert = alert_service.process_reading_telemetry(reading)
    assert alert is not None
    assert alert.metric == "light"
    assert alert.severity == "critical"
    assert "Light Intensity critical: 3,500 Lux — Maximum: 2,000 Lux" in alert.description

def test_every_supported_metric_boundaries():
    """Verify threshold evaluation for min and max bounds for all metrics."""
    for metric, cfg in SENSOR_THRESHOLDS.items():
        # Inside normal bounds
        res_mid = evaluate_reading_threshold(metric, (cfg.optimal_min + cfg.optimal_max) / 2)
        assert res_mid.is_valid
        assert not res_mid.is_violation
        assert res_mid.status == "healthy"

        # Above optimalMax
        res_high = evaluate_reading_threshold(metric, cfg.optimal_max + 0.5)
        assert res_high.is_valid
        assert res_high.is_violation
        assert res_high.violation_direction == "high"

        # Below optimalMin
        res_low = evaluate_reading_threshold(metric, cfg.optimal_min - 0.5)
        assert res_low.is_valid
        assert res_low.is_violation
        assert res_low.violation_direction == "low"

def test_invalid_missing_stale_readings_do_not_alert():
    """Malformed or invalid readings must be rejected without alerting."""
    invalid_cases = [
        ("temperature", None),
        ("temperature", "bad_value"),
        ("temperature", float("nan")),
        ("temperature", float("inf")),
        ("temperature", 200.0), # Outside physical bounds
        ("humidity", -10.0), # Outside physical bounds
        ("ph", 18.0), # Outside physical bounds
    ]

    for metric, val in invalid_cases:
        res = evaluate_reading_threshold(metric, val)
        assert not res.is_valid
        assert not res.is_violation

        # Ingestion through service must also return None
        reading = SensorReading(
            id="r-invalid",
            sensor_id="s-bad",
            farm_id="farm-test",
            metric=metric,
            value=val, # type: ignore
            unit="unit",
        )
        alert = alert_service.process_reading_telemetry(reading)
        assert alert is None

def test_duplicate_alert_suppression():
    """Consecutive readings exceeding threshold must produce only 1 alert."""
    reading1 = SensorReading(
        id="r-1",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=33.5,
        unit="°C",
    )
    first_alert = alert_service.process_reading_telemetry(reading1)
    assert first_alert is not None
    assert len(db.alerts) == 1

    # Second reading with same/similar high value
    reading2 = SensorReading(
        id="r-2",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=34.0,
        unit="°C",
    )
    second_alert = alert_service.process_reading_telemetry(reading2)
    # Must be suppressed!
    assert second_alert is None
    # Still only 1 alert exists
    assert len(db.alerts) == 1

    # Third reading still high
    reading3 = SensorReading(
        id="r-3",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=33.8,
        unit="°C",
    )
    third_alert = alert_service.process_reading_telemetry(reading3)
    assert third_alert is None
    assert len(db.alerts) == 1

def test_recovery_and_subsequent_realerting():
    """When reading returns to normal, alert is marked resolved. Subsequent violation triggers new alert."""
    # 1. Trigger high temperature alert
    r_high1 = SensorReading(
        id="r-h1",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=34.0,
        unit="°C",
    )
    alert1 = alert_service.process_reading_telemetry(r_high1)
    assert alert1 is not None
    assert not alert1.is_resolved

    # 2. Reading recovers to normal (25°C, well below optimalMax 30 - hysteresis 0.5)
    r_normal = SensorReading(
        id="r-norm",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=25.0,
        unit="°C",
    )
    alert_service.process_reading_telemetry(r_normal)
    # Original alert must now be marked resolved
    assert alert1.is_resolved is True

    # 3. Reading violates threshold again after recovery
    r_high2 = SensorReading(
        id="r-h2",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=33.5,
        unit="°C",
    )
    alert2 = alert_service.process_reading_telemetry(r_high2)
    assert alert2 is not None
    assert alert2.id != alert1.id
    assert not alert2.is_resolved
    assert len(db.alerts) == 2

def test_multiple_sensors_violating_thresholds_simultaneously():
    """Simultaneous violations on different sensors must produce separate alerts."""
    r_temp = SensorReading(
        id="r-multi-temp",
        sensor_id="s-temp",
        farm_id="farm-test",
        metric="temperature",
        value=34.5,
        unit="°C",
    )
    r_hum = SensorReading(
        id="r-multi-hum",
        sensor_id="s-hum",
        farm_id="farm-test",
        metric="humidity",
        value=35.0,
        unit="%",
    )
    r_soil = SensorReading(
        id="r-multi-soil",
        sensor_id="s-soil",
        farm_id="farm-test",
        metric="soilMoisture",
        value=20.0,
        unit="%",
    )

    alert_temp = alert_service.process_reading_telemetry(r_temp)
    alert_hum = alert_service.process_reading_telemetry(r_hum)
    alert_soil = alert_service.process_reading_telemetry(r_soil)

    assert alert_temp is not None
    assert alert_hum is not None
    assert alert_soil is not None
    assert alert_temp.metric == "temperature"
    assert alert_hum.metric == "humidity"
    assert alert_soil.metric == "soilMoisture"
    assert len(db.alerts) == 3

def test_evaluate_threshold_api_endpoint(client):
    """Test the POST /api/v1/alerts/evaluate REST endpoint."""
    payload = {
        "metric": "temperature",
        "value": 34.2,
    }
    response = client.post("/api/v1/alerts/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["isValid"] is True
    assert data["isViolation"] is True
    assert data["status"] == "warning"
    assert "High temperature detected" in data["notificationBody"]
    assert "> 30.0 °C" in data["thresholdValueFormatted"]
