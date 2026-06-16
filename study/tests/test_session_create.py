import copy

import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.models import StudySession, Problem, ProblemParticipant
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c, u

def test_create_session_returns_slug():
    c, _ = _client()
    resp = c.post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert body["session_id"] == "2026-06-13-sqlp-실전문제-1"

def test_create_persists_problem_and_participant():
    c, _ = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    s = StudySession.objects.get(id="2026-06-13-sqlp-실전문제-1")
    assert s.problems.count() == 1
    p = s.problems.first()
    assert p.problem_number == 1
    assert {c.name for c in p.concepts.all()} == {"JOIN", "OUTER JOIN"}
    pp = p.participants.get(name="세은")
    assert pp.understanding == "애매"
    assert pp.concepts_missed == ["NULL 처리"]

def test_duplicate_session_rejected():
    c, _ = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 409
    assert resp.json()["code"] == "DUPLICATE_SESSION"

def test_different_problem_set_not_duplicate():
    c, _ = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    other = copy.deepcopy(PAYLOAD)
    other["problems"][0]["problem_number"] = 2  # same date+book, different number set
    resp = c.post("/api/sessions/", other, format="json")
    assert resp.status_code == 201

def test_participant_linked_to_member_by_name():
    c, u = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    pp = ProblemParticipant.objects.get(name="세은")
    assert pp.member_id == u.id

def test_create_requires_auth():
    resp = APIClient().post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 401
