import pytest
from rest_framework.test import APIClient
from accounts.models import User, StudyGroup
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_wrong_answers_list():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/wrong-answers/")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert item["person"] == "세은"
    assert item["reviewRequired"] is True
    assert item["done"] is False
    assert item["problemNumber"] == 1
    assert item["book"] == "SQLP 실전문제"
    assert item["sessionDate"] == "2026-06-13"
    assert set(item["concepts"]) == {"JOIN", "OUTER JOIN"}
    assert item["missed"] == ["NULL 처리"]
    assert "id" in item and "sessionId" in item and "problemId" in item

def test_mark_done():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    wid = c.get("/api/wrong-answers/").json()[0]["id"]
    resp = c.patch(f"/api/wrong-answers/{wid}/", {"done": True}, format="json")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "id": wid, "done": True}
    assert c.get("/api/wrong-answers/").json()[0]["done"] is True

def test_mark_done_missing_404():
    c = _client()
    resp = c.patch("/api/wrong-answers/nope::nobody/", {"done": True}, format="json")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"

def test_wrong_answers_group_scoped():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    other = StudyGroup.objects.create(name="other", slug="other")
    u2 = User.objects.create_user(email="z@z.com", name="z", password="pw12345", group=other)
    c2 = APIClient(); c2.force_authenticate(u2)
    assert c2.get("/api/wrong-answers/").json() == []

def test_wrong_answers_requires_auth():
    assert APIClient().get("/api/wrong-answers/").status_code == 401

def test_mark_done_rejects_non_bool():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    wid = c.get("/api/wrong-answers/").json()[0]["id"]
    resp = c.patch(f"/api/wrong-answers/{wid}/", {"done": "false"}, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_mark_done_requires_done_field():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    wid = c.get("/api/wrong-answers/").json()[0]["id"]
    resp = c.patch(f"/api/wrong-answers/{wid}/", {}, format="json")
    assert resp.status_code == 400

def test_mark_done_false_unsets():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    wid = c.get("/api/wrong-answers/").json()[0]["id"]
    c.patch(f"/api/wrong-answers/{wid}/", {"done": True}, format="json")
    resp = c.patch(f"/api/wrong-answers/{wid}/", {"done": False}, format="json")
    assert resp.status_code == 200
    assert resp.json()["done"] is False

def test_mark_done_name_with_slash_is_routable():
    import copy
    c = _client()
    p = copy.deepcopy(PAYLOAD)
    p["problems"][0]["participants"][0]["name"] = "세은/수철"
    c.post("/api/sessions/", p, format="json")
    item = c.get("/api/wrong-answers/").json()[0]
    assert item["person"] == "세은/수철"
    resp = c.patch(f"/api/wrong-answers/{item['id']}/", {"done": True}, format="json")
    assert resp.status_code == 200
    assert resp.json()["done"] is True
