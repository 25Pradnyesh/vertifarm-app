def test_login_email_success(client):
    response = client.post("/api/v1/auth/login", json={"email": "operator@vertifarm.io"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "operator@vertifarm.io"

def test_signup_email_success(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={"name": "Sarah Connor", "email": "sarah@vertifarm.io", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["name"] == "Sarah Connor"
    assert data["user"]["email"] == "sarah@vertifarm.io"

def test_google_auth_dev_token(client):
    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "dev-token-usr-google-qa"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == "usr-google-qa"
    assert data["user"]["authProvider"] == "google"

def test_get_current_user_profile(client, auth_headers, test_user):
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name

def test_get_current_user_unauthorized(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "detail" in response.json()

def test_update_current_user_profile(client, auth_headers):
    response = client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"name": "Updated Grower Name", "farmName": "Hydroponic Delta"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Grower Name"
    assert data["farmName"] == "Hydroponic Delta"
