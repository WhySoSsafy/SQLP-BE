import pytest
from rest_framework.test import APIClient
from accounts.models import User, StudyGroup

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

PA = {
    "book": "SQLP 실전문제",
    "problems": [{
        "problem_number": 1, "subject_area": "SQL 기본 및 활용",
        "concepts": ["JOIN", "OUTER JOIN"], "estimated_difficulty": "중",
        "frequency": "높음", "priority": 1
    }],
}

def test_register_and_list():
    c = _client()
    resp = c.post("/api/problem-analysis/", PA, format="json")
    assert resp.status_code == 201
    assert resp.json() == {"ok": True, "created_count": 1}
    listed = c.get("/api/problem-analysis/")
    assert listed.status_code == 200
    item = listed.json()[0]
    assert item["book"] == "SQLP 실전문제"
    assert item["problem_number"] == 1
    assert item["subject_area"] == "SQL 기본 및 활용"
    assert item["estimated_difficulty"] == "중"
    assert item["frequency"] == "높음"
    assert item["priority"] == 1
    assert item["concepts"] == ["JOIN", "OUTER JOIN"]
    assert "id" in item

def test_register_multiple():
    c = _client()
    payload = {"book": "B", "problems": [
        {"problem_number": 1, "subject_area": "x", "concepts": [], "estimated_difficulty": "하", "frequency": "낮음", "priority": 2},
        {"problem_number": 2, "subject_area": "y", "concepts": ["Z"], "estimated_difficulty": "상", "frequency": "높음", "priority": 1},
    ]}
    resp = c.post("/api/problem-analysis/", payload, format="json")
    assert resp.json()["created_count"] == 2
    # ordered by priority then problem_number
    items = c.get("/api/problem-analysis/").json()
    assert [i["priority"] for i in items] == [1, 2]

def test_list_group_scoped():
    c = _client()
    c.post("/api/problem-analysis/", PA, format="json")
    other = StudyGroup.objects.create(name="other", slug="other")
    u2 = User.objects.create_user(email="z@z.com", name="z", password="pw12345", group=other)
    c2 = APIClient(); c2.force_authenticate(u2)
    assert c2.get("/api/problem-analysis/").json() == []

def test_register_validation_error():
    c = _client()
    bad = {"book": "B", "problems": [{"subject_area": "x"}]}  # missing required fields
    resp = c.post("/api/problem-analysis/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_requires_auth():
    assert APIClient().get("/api/problem-analysis/").status_code == 401
