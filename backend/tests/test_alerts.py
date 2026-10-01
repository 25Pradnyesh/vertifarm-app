def test_list_alerts(client, auth_headers):
    response = client.get("/api/v1/alerts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "severity" in data[0]
    assert "title" in data[0]

def test_list_alerts_filter_severity(client, auth_headers):
    response = client.get("/api/v1/alerts?severity=critical", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(a["severity"] == "critical" for a in data)

def test_get_alert_by_id(client, auth_headers):
    response = client.get("/api/v1/alerts/alert-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "alert-1"
    assert data["severity"] == "critical"

def test_resolve_alert(client, auth_headers):
    response = client.post("/api/v1/alerts/alert-1/resolve", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "alert-1"
    assert data["isResolved"] is True
    assert "resolvedAt" in data
