import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_calendar_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/calendar/?year=2026&month=6")
    assert resp.status_code == 200
    body = resp.json()
    assert body["year"] == 2026 and body["month"] == 6
    assert isinstance(body["days"], list)
    assert "monthlyProblemCount" in body and "weeklyProblemCount" in body and "studyStreak" in body
    day = next(d for d in body["days"] if d["date"] == "2026-06-13")
    assert day["problemCount"] == 1
    assert day["averageUnderstanding"] == 65
    assert day["reviewRequiredCount"] == 1
    assert "OUTER JOIN" in day["mainConcepts"]
    assert body["monthlyProblemCount"] == 1

def test_calendar_other_month_empty():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    body = c.get("/api/calendar/?year=2026&month=7").json()
    assert body["days"] == []
    assert body["monthlyProblemCount"] == 0

def test_calendar_invalid_params_400():
    c = _client()
    resp = c.get("/api/calendar/?year=abc&month=6")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_calendar_invalid_year_400():
    c = _client()
    resp = c.get("/api/calendar/?year=0&month=6")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_calendar_requires_auth():
    assert APIClient().get("/api/calendar/").status_code == 401

def test_calendar_weekly_excludes_future_sessions():
    from datetime import timedelta
    from django.utils import timezone
    from accounts.models import StudyGroup
    from study.models import StudySession, Problem
    from analytics.services.calendar import calendar_data
    g = StudyGroup.get_default()
    today = timezone.now().date()
    future = today + timedelta(days=3)
    for i, d in enumerate([today, future]):
        s = StudySession.objects.create(id=f"wk{i}", group=g, session_date=d, book="b")
        Problem.objects.create(id=f"wk{i}-p1", session=s, problem_number=1, subject_area="x")
    data = calendar_data(g, today.year, today.month)
    assert data["weeklyProblemCount"] >= 1
    # When the future session falls in the same calendar month, it inflates the
    # monthly count but must NOT be in the weekly count.
    if future.month == today.month and future.year == today.year:
        assert data["weeklyProblemCount"] == 1
        assert data["monthlyProblemCount"] == 2
