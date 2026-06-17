import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

def test_validation_error_envelope():
    client = APIClient()
    resp = client.post("/api/auth/register/", {"email": "bad"}, format="json")
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["code"] == "VALIDATION_ERROR"
    assert isinstance(body["errors"], list)
    assert "path" in body["errors"][0] and "message" in body["errors"][0]

def test_auth_failure_envelope():
    client = APIClient()
    resp = client.get("/api/users/me/")
    assert resp.status_code in (401, 403)
    assert resp.json()["ok"] is False
