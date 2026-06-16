import copy
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD
from analytics.services.recommendations import REVIEW_REASON

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_recommendations_shape_and_filter():
    # Build a session where 세은 is 모름+wrong => score 0 => recommended
    c = _client()
    p = copy.deepcopy(PAYLOAD)
    part = p["problems"][0]["participants"][0]
    part["understanding"] = "모름"
    part["is_correct"] = False
    c.post("/api/sessions/", p, format="json")
    resp = c.get("/api/recommendations/review/")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    item = items[0]
    for key in ("concept", "subject", "reason", "score"):
        assert key in item
    assert item["score"] == 0
    assert item["reason"] == REVIEW_REASON

def test_recommendations_excludes_non_weak():
    # default PAYLOAD: 세은 애매+correct = 65 => not recommended => empty
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    assert c.get("/api/recommendations/review/").json() == []

def test_recommendations_requires_auth():
    assert APIClient().get("/api/recommendations/review/").status_code == 401
