import pytest
from rest_framework.test import APIClient
from accounts.models import User, StudyGroup
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_concept_list():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/concepts/")
    assert resp.status_code == 200
    items = resp.json()
    names = {i["name"] for i in items}
    assert "OUTER JOIN" in names
    item = next(i for i in items if i["name"] == "OUTER JOIN")
    assert "id" in item and "subject" in item and "summary" in item
    assert item["myUnderstanding"] == 65
    assert item["reviewRecommended"] is False

def test_concept_detail():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    concepts = c.get("/api/concepts/").json()
    outer_join = next(i for i in concepts if i["name"] == "OUTER JOIN")
    cid = outer_join["id"]
    resp = c.get(f"/api/concepts/{cid}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == cid
    assert body["name"] == "OUTER JOIN"
    assert "subject" in body
    assert body["myUnderstanding"] == 65
    assert body["reviewRecommended"] is False
    assert "frequentQuestionTypes" in body
    assert "confusingPoints" in body
    assert "wrongPatterns" in body
    assert "relatedProblems" in body
    assert "myUnderstanding" in body
    assert "reviewRecommended" in body
    if body["relatedProblems"]:
        rp = body["relatedProblems"][0]
        assert "sessionId" in rp and "problemNumber" in rp
        assert "person" in rp
        assert "understanding" in rp and "reviewRequired" in rp

def test_concept_detail_other_group_404():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    cid = c.get("/api/concepts/").json()[0]["id"]
    other = StudyGroup.objects.create(name="other", slug="other")
    u2 = User.objects.create_user(email="z@z.com", name="z", password="pw12345", group=other)
    c2 = APIClient(); c2.force_authenticate(u2)
    assert c2.get(f"/api/concepts/{cid}/").status_code == 404

def test_concepts_require_auth():
    assert APIClient().get("/api/concepts/").status_code == 401
