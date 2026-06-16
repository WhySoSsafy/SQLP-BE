import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

def test_register_creates_user():
    client = APIClient()
    resp = client.post("/api/auth/register/", {
        "name": "세은", "email": "seun@example.com", "password": "password123"
    }, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert body["user"]["email"] == "seun@example.com"
    assert "id" in body["user"]

def test_me_requires_auth_and_returns_profile():
    from accounts.models import User
    user = User.objects.create_user(email="seun@example.com", name="세은", password="password123")
    client = APIClient()
    assert client.get("/api/users/me/").status_code == 401
    client.force_authenticate(user)
    resp = client.get("/api/users/me/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "seun@example.com"
    assert body["name"] == "세은"
    assert "profile_label" in body

def test_login_returns_tokens_and_user():
    from accounts.models import User
    User.objects.create_user(email="seun@example.com", name="세은", password="password123")
    client = APIClient()
    resp = client.post("/api/auth/login/", {
        "email": "seun@example.com", "password": "password123"
    }, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert "access" in body and "refresh" in body
    assert body["user"]["email"] == "seun@example.com"

def test_login_wrong_password_returns_401():
    from accounts.models import User
    User.objects.create_user(email="seun@example.com", name="세은", password="password123")
    client = APIClient()
    resp = client.post("/api/auth/login/",
        {"email": "seun@example.com", "password": "wrong"}, format="json")
    assert resp.status_code == 401
