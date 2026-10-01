def test_list_farms_authenticated(client, auth_headers):
    response = client.get("/api/v1/farms", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "name" in data[0]
    assert "sensorCount" in data[0]
    assert "zoneCount" in data[0]

def test_get_farm_by_id(client, auth_headers):
    response = client.get("/api/v1/farms/farm-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "farm-1"
    assert data["name"] == "Greenhouse 1"

def test_get_nonexistent_farm(client, auth_headers):
    response = client.get("/api/v1/farms/farm-nonexistent", headers=auth_headers)
    assert response.status_code == 404

def test_create_farm(client, auth_headers):
    payload = {
        "name": "Vertical Aero Tower",
        "location": "Bengaluru, Karnataka, India",
        "isActive": True,
    }
    response = client.post("/api/v1/farms", headers=auth_headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Vertical Aero Tower"
    assert data["location"] == "Bengaluru, Karnataka, India"
    assert data["isActive"] is True
    assert "id" in data

def test_list_farm_zones(client, auth_headers):
    response = client.get("/api/v1/farms/farm-1/zones", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["crop"] == "Tomato"
