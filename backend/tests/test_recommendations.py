def test_list_recommendations(client, auth_headers):
    response = client.get("/api/v1/recommendations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "category" in data[0]
    assert "priority" in data[0]

def test_list_recommendations_filter_tab(client, auth_headers):
    response = client.get("/api/v1/recommendations?tab=forYou", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(r["tab"] == "forYou" for r in data)

def test_list_recommendations_filter_category(client, auth_headers):
    response = client.get("/api/v1/recommendations?category=irrigation", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(r["category"] == "irrigation" for r in data)
