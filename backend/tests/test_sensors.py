def test_list_sensors_authenticated(client, auth_headers):
    response = client.get("/api/v1/sensors", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    sensor = data[0]
    assert "name" in sensor
    assert "metric" in sensor
    assert "status" in sensor
    assert "zoneName" in sensor

def test_get_sensor_by_id(client, auth_headers):
    response = client.get("/api/v1/sensors/s-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "s-1"
    assert data["metric"] == "temperature"

def test_get_nonexistent_sensor(client, auth_headers):
    response = client.get("/api/v1/sensors/s-nonexistent", headers=auth_headers)
    assert response.status_code == 404

def test_create_sensor(client, auth_headers):
    payload = {
        "name": "CO2 Sensor",
        "type": "MG811",
        "metric": "temperature",
        "zoneId": "z-1",
        "status": "active",
        "batteryLevel": 95,
    }
    response = client.post("/api/v1/sensors", headers=auth_headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "CO2 Sensor"
    assert data["type"] == "MG811"
    assert data["batteryLevel"] == 95
