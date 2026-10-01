def test_list_scans(client, auth_headers):
    response = client.get("/api/v1/ai/scans", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "diseaseName" in data[0]
    assert "confidence" in data[0]

def test_get_scan_by_id(client, auth_headers):
    response = client.get("/api/v1/ai/scans/scan-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "scan-1"
    assert data["diseaseName"] == "Leaf Spot"

def test_get_camera_status(client, auth_headers):
    response = client.get("/api/v1/ai/camera/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "cameraId" in data
    assert "imageUrl" in data
    assert "isLive" in data

def test_trigger_camera_capture(client, auth_headers):
    response = client.post("/api/v1/ai/camera/capture", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["queued"] is True
    assert "job_id" in data
