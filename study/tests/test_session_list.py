import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_list_returns_summary_fields():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/sessions/")
    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["id"] == "2026-06-13-sqlp-실전문제-1"
    assert row["book"] == "SQLP 실전문제"
    assert row["problem_count"] == 1
    assert row["review_required_count"] == 1
    assert "average_understanding" in row
    assert set(row["speakers"]) >= {"세은"}
    assert "created_at" in row

def test_list_search_filters_by_book():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    assert len(c.get("/api/sessions/?search=SQLP").json()) == 1
    assert len(c.get("/api/sessions/?search=없는책").json()) == 0

def test_list_date_range_filter():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    assert len(c.get("/api/sessions/?date_from=2026-06-01&date_to=2026-06-30").json()) == 1
    assert len(c.get("/api/sessions/?date_from=2026-07-01").json()) == 0

def test_list_requires_auth():
    resp = APIClient().get("/api/sessions/")
    assert resp.status_code == 401

def test_list_group_scoped():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    from accounts.models import StudyGroup
    other = StudyGroup.objects.create(name="other", slug="other")
    u2 = User.objects.create_user(email="z@z.com", name="z", password="pw12345", group=other)
    c2 = APIClient(); c2.force_authenticate(u2)
    assert len(c2.get("/api/sessions/").json()) == 0

def test_list_understanding_gap_excludes_mid_scores():
    # PAYLOAD's only participant 세은 is 애매(50)+correct => score 65,
    # which is neither high (>=70) nor low (<50): both filters return empty.
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    assert len(c.get("/api/sessions/?understanding=high").json()) == 0
    assert len(c.get("/api/sessions/?understanding=low").json()) == 0

def test_list_invalid_date_returns_400():
    c = _client()
    resp = c.get("/api/sessions/?date_from=notadate")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"
