import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure backend package is in python search path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.core.security import create_access_token
from app.db.session import db

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(scope="session")
def test_user():
    return db.users["usr-default"]

@pytest.fixture(scope="session")
def auth_headers(test_user):
    token = create_access_token({
        "sub": test_user.id,
        "email": test_user.email,
        "name": test_user.name,
        "role": test_user.role,
    })
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def other_user():
    return db.get_or_create_user({
        "id": "usr-other-grower",
        "email": "other@vertifarm.io",
        "name": "Other Grower",
        "role": "Farm Owner",
        "farm_name": "Other Greenhouse",
    })

@pytest.fixture
def other_auth_headers(other_user):
    token = create_access_token({
        "sub": other_user.id,
        "email": other_user.email,
        "name": other_user.name,
        "role": other_user.role,
    })
    return {"Authorization": f"Bearer {token}"}
