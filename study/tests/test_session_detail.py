import pytest
from rest_framework.test import APIClient
from accounts.models import User, StudyGroup
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_detail_returns_nested_problems():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    resp = c.get(f"/api/sessions/{sid}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == sid
    assert body["session_date"] == "2026-06-13"
    assert body["book"] == "SQLP 실전문제"
    assert set(body["speakers"]) == {"세은", "수철"}
    prob = body["problems"][0]
    assert prob["problem_number"] == 1
    assert set(prob["concepts"]) == {"JOIN", "OUTER JOIN"}
    part = prob["participants"][0]
    assert part["name"] == "세은"
    assert part["understanding"] == "애매"
    assert part["concepts_missed"] == ["NULL 처리"]
    assert part["review_required"] is True

def test_delete_session():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    resp = c.delete(f"/api/sessions/{sid}/")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert c.get(f"/api/sessions/{sid}/").status_code == 404

def test_detail_missing_404():
    c = _client()
    resp = c.get("/api/sessions/nonexistent-id/")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"

def test_detail_other_group_404():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    other = StudyGroup.objects.create(name="other", slug="other")
    u2 = User.objects.create_user(email="z@z.com", name="z", password="pw12345", group=other)
    c2 = APIClient(); c2.force_authenticate(u2)
    assert c2.get(f"/api/sessions/{sid}/").status_code == 404
    assert c2.delete(f"/api/sessions/{sid}/").status_code == 404

def test_detail_requires_auth():
    resp = APIClient().get("/api/sessions/x/")
    assert resp.status_code == 401

def test_delete_missing_404():
    c = _client()
    resp = c.delete("/api/sessions/nonexistent-id/")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"
