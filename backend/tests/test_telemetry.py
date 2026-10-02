def test_get_telemetry_summaries(client, auth_headers):
    response = client.get("/api/v1/telemetry/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 6
    metrics = {item["metric"] for item in data}
    assert "temperature" in metrics
    assert "humidity" in metrics
    assert "soilMoisture" in metrics
    assert "ph" in metrics
    assert "tds" in metrics
    assert "light" in metrics

def test_get_farm_health_status(client, auth_headers):
    response = client.get("/api/v1/telemetry/health", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "warning", "critical")
    assert "message" in data

def test_get_telemetry_by_metric(client, auth_headers):
    response = client.get("/api/v1/telemetry/temperature", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "temperature"
    assert "currentValue" in data
    assert "unit" in data
    assert "trend" in data
    assert len(data["trend"]) > 0

def test_get_telemetry_invalid_metric(client, auth_headers):
    response = client.get("/api/v1/telemetry/unknown-metric", headers=auth_headers)
    assert response.status_code == 404

def test_get_latest_telemetry(client, auth_headers):
    response = client.get("/api/v1/telemetry/latest", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_readings_history(client, auth_headers):
    response = client.get("/api/v1/telemetry/readings", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
