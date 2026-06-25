import pytest
from rest_framework.test import APIClient
from accounts.models import User

from concepts.models import Concept

pytestmark = pytest.mark.django_db


def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient()
    c.force_authenticate(u)
    return c, u


def test_create_concept_201():
    """POST with 'title' alias creates the concept and returns 201 with correct fields."""
    client, user = _client()
    payload = {
        "title": "옵티마이저",
        "subject": "SQLP",
        "summary": "실행계획 선택",
        "confusingPoints": ["인덱스 오해"],
    }
    resp = client.post("/api/concepts/", payload, format="json")
    assert resp.status_code == 201, resp.json()

    # Concept was actually persisted for the user's group
    assert Concept.objects.filter(group=user.group, name="옵티마이저").exists()

    body = resp.json()
    assert body["name"] == "옵티마이저"
    assert body["confusingPoints"] == ["인덱스 오해"]
    assert body["subject"] == "SQLP"
    assert body["summary"] == "실행계획 선택"
    assert "id" in body


def test_upsert_same_name_updates_no_duplicate():
    """POST again with the same name updates the record; no duplicate is created."""
    client, user = _client()
    client.post(
        "/api/concepts/",
        {"title": "옵티마이저", "subject": "SQLP", "summary": "처음 요약"},
        format="json",
    )

    resp = client.post(
        "/api/concepts/",
        {"name": "옵티마이저", "summary": "업데이트된 요약"},
        format="json",
    )
    assert resp.status_code in {200, 201}, resp.json()

    # No duplicate — exactly one record
    assert Concept.objects.filter(name="옵티마이저").count() == 1

    # Summary was updated
    concept = Concept.objects.get(name="옵티마이저")
    assert concept.summary == "업데이트된 요약"


def test_blank_name_returns_400():
    """POST with blank name field returns 400."""
    client, _ = _client()
    resp = client.post("/api/concepts/", {"name": ""}, format="json")
    assert resp.status_code == 400


def test_non_string_name_returns_400_not_500():
    """A non-string name (number/list) must return 400, never crash with 500."""
    client, _ = _client()
    for bad in (123, [], {}):
        resp = client.post("/api/concepts/", {"name": bad}, format="json")
        assert resp.status_code == 400, f"name={bad!r} -> {resp.status_code}"


def test_null_subject_summary_stored_as_empty_string():
    """Explicit JSON null for subject/summary is normalized to '' (non-null fields)."""
    client, user = _client()
    resp = client.post(
        "/api/concepts/",
        {"name": "널테스트", "subject": None, "summary": None},
        format="json",
    )
    assert resp.status_code == 201
    concept = Concept.objects.get(name="널테스트")
    assert concept.subject == ""
    assert concept.summary == ""


def test_missing_name_returns_400():
    """POST without name or title returns 400."""
    client, _ = _client()
    resp = client.post("/api/concepts/", {"subject": "SQLP"}, format="json")
    assert resp.status_code == 400


def test_get_detail_after_create():
    """GET /api/concepts/<id>/ after create returns the concept with correct name."""
    client, user = _client()
    create_resp = client.post(
        "/api/concepts/",
        {"name": "옵티마이저", "subject": "SQLP", "summary": "실행계획 선택"},
        format="json",
    )
    assert create_resp.status_code == 201
    concept_id = create_resp.json()["id"]

    detail_resp = client.get(f"/api/concepts/{concept_id}/")
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["name"] == "옵티마이저"
    assert body["id"] == concept_id


def test_create_ignores_extra_keys():
    """Extra unknown keys (e.g. sqlExamples) are silently ignored; request succeeds."""
    client, user = _client()
    payload = {
        "name": "집계함수",
        "subject": "SQL",
        "sqlExamples": ["SELECT COUNT(*) FROM t"],
        "keywords": ["COUNT", "SUM"],
        "easyExplanation": "그냥 세는 것",
    }
    resp = client.post("/api/concepts/", payload, format="json")
    assert resp.status_code == 201


def test_create_requires_auth():
    """Unauthenticated POST returns 401."""
    resp = APIClient().post("/api/concepts/", {"name": "테스트"}, format="json")
    assert resp.status_code == 401
