import pytest
from rest_framework.test import APIClient
from accounts.models import User, StudyGroup
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_comparison_shape():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    resp = c.get(f"/api/study-comparison/?session_id={sid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sessionId"] == sid
    assert body["book"] == "SQLP 실전문제"
    assert body["sessionDate"] == "2026-06-13"
    assert isinstance(body["participants"], list)
    p = next(x for x in body["participants"] if x["name"] == "세은")
    assert p["averageUnderstanding"] == 65
    assert p["correctCount"] == 1
    assert p["reviewRequiredCount"] == 1
    assert "NULL 처리" in p["weakConcepts"]   # from concepts_missed
    assert isinstance(body["problems"], list)
    prob = body["problems"][0]
    assert prob["problemNumber"] == 1
    assert set(prob["concepts"]) == {"JOIN", "OUTER JOIN"}
    pp = prob["participants"][0]
    for key in ("name", "isCorrect", "understanding", "reviewRequired"):
        assert key in pp

def test_comparison_missing_session_id_400():
    c = _client()
    resp = c.get("/api/study-comparison/")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_comparison_other_group_404():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    other = StudyGroup.objects.create(name="other", slug="other")
    u2 = User.objects.create_user(email="z@z.com", name="z", password="pw12345", group=other)
    c2 = APIClient(); c2.force_authenticate(u2)
    assert c2.get(f"/api/study-comparison/?session_id={sid}").status_code == 404

def test_comparison_requires_auth():
    assert APIClient().get("/api/study-comparison/?session_id=x").status_code == 401
