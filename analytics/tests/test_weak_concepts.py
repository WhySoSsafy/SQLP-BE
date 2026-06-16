import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_weak_concepts_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/weak-concepts/")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    item = next(i for i in items if i["name"] == "OUTER JOIN")
    for key in ("name", "subject", "totalProblems", "weakCountByParticipant",
                "scoreByParticipant", "averageScore", "lastReviewDate", "recommend"):
        assert key in item
    # 세은 애매+correct = 65; review_required=True so counted weak for 세은
    assert item["scoreByParticipant"]["세은"] == 65
    assert item["weakCountByParticipant"]["세은"] == 1
    assert item["averageScore"] == 65
    assert item["totalProblems"] == 1
    assert item["lastReviewDate"] == "2026-06-13"
    assert item["recommend"] is False  # 65 >= 50

def test_weak_concepts_sorted_by_score_asc():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    items = c.get("/api/weak-concepts/").json()
    scores = [i["averageScore"] for i in items]
    assert scores == sorted(scores)

def test_weak_concepts_group_scoped_and_auth():
    assert APIClient().get("/api/weak-concepts/").status_code == 401
