import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_growth_report_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/reports/growth/?period=monthly")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("period", "problemCount", "averageUnderstanding",
                "reviewRequiredCount", "improvedConcepts", "stillWeakConcepts", "trend"):
        assert key in body
    assert body["period"] == "monthly"
    assert body["problemCount"] == 1
    assert body["averageUnderstanding"] == 65
    assert body["reviewRequiredCount"] == 1
    assert isinstance(body["trend"], list)
    assert body["trend"][0] == {"date": "2026-06-13", "averageUnderstanding": 65}
    # OUTER JOIN avg 65 >= 50: not still-weak; not >=70: not improved
    assert "OUTER JOIN" not in body["stillWeakConcepts"]

def test_growth_report_default_period():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    body = c.get("/api/reports/growth/").json()
    assert body["period"] == "monthly"

def test_growth_report_empty_group():
    c = _client()
    body = c.get("/api/reports/growth/").json()
    assert body["problemCount"] == 0
    assert body["averageUnderstanding"] == 0
    assert body["trend"] == []
    assert body["improvedConcepts"] == []
    assert body["stillWeakConcepts"] == []

def test_growth_report_requires_auth():
    assert APIClient().get("/api/reports/growth/").status_code == 401
