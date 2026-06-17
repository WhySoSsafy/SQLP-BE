import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_dashboard_summary_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/dashboard/summary/")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("weeklyProblemCount", "reviewRequiredCount", "averageUnderstanding",
                "studyStreak", "recommendations", "recentSessions"):
        assert key in body
    assert isinstance(body["recommendations"], list)
    assert isinstance(body["recentSessions"], list)
    assert isinstance(body["studyStreak"], int)
    assert isinstance(body["weeklyProblemCount"], int)
    # deterministic regardless of today's date:
    assert body["reviewRequiredCount"] == 1            # 세은 review_required=True
    assert body["averageUnderstanding"] == 65          # 애매+correct
    assert len(body["recentSessions"]) == 1
    rs = body["recentSessions"][0]
    for key in ("id", "date", "book", "problemCount", "averageUnderstanding"):
        assert key in rs
    assert rs["problemCount"] == 1

def test_dashboard_empty_group():
    c = _client()
    resp = c.get("/api/dashboard/summary/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["weeklyProblemCount"] == 0
    assert body["reviewRequiredCount"] == 0
    assert body["averageUnderstanding"] == 0
    assert body["studyStreak"] == 0
    assert body["recentSessions"] == []

def test_dashboard_requires_auth():
    assert APIClient().get("/api/dashboard/summary/").status_code == 401


def test_dashboard_recent_sessions_capped_at_5():
    import copy
    c = _client()
    for n in range(1, 7):  # 6 distinct sessions (different problem-number sets => distinct dedup keys)
        p = copy.deepcopy(PAYLOAD)
        p["problems"][0]["problem_number"] = n
        c.post("/api/sessions/", p, format="json")
    body = c.get("/api/dashboard/summary/").json()
    assert len(body["recentSessions"]) == 5


def test_study_streak_counts_consecutive_days():
    from datetime import timedelta
    from django.utils import timezone
    from accounts.models import StudyGroup
    from study.models import StudySession
    from analytics.services.dashboard import _study_streak
    g = StudyGroup.get_default()
    today = timezone.now().date()
    for i in range(3):  # today, today-1, today-2
        d = today - timedelta(days=i)
        StudySession.objects.create(id=f"streak-{i}", group=g, session_date=d, book="b")
    assert _study_streak(g) == 3


def test_study_streak_zero_when_gap_before_yesterday():
    from datetime import timedelta
    from django.utils import timezone
    from accounts.models import StudyGroup
    from study.models import StudySession
    from analytics.services.dashboard import _study_streak
    g = StudyGroup.get_default()
    today = timezone.now().date()
    # only a session 2 days ago: neither today nor yesterday => streak 0
    StudySession.objects.create(id="gap-1", group=g, session_date=today - timedelta(days=2), book="b")
    assert _study_streak(g) == 0


def test_dashboard_weekly_excludes_future_sessions():
    from datetime import timedelta
    from django.utils import timezone
    from accounts.models import StudyGroup
    from study.models import StudySession, Problem
    from analytics.services.dashboard import dashboard_summary
    g = StudyGroup.get_default()
    today = timezone.now().date()
    for i, d in enumerate([today, today + timedelta(days=3)]):
        s = StudySession.objects.create(id=f"dw{i}", group=g, session_date=d, book="b")
        Problem.objects.create(id=f"dw{i}-p1", session=s, problem_number=1, subject_area="x")
    data = dashboard_summary(g)
    # only the today session counts toward the weekly total; the +3-day future one does not
    assert data["weeklyProblemCount"] == 1
