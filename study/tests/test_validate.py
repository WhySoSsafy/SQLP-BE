import pytest
from rest_framework.test import APIClient
from accounts.models import User

pytestmark = pytest.mark.django_db

PAYLOAD = {
    "session_date": "2026-06-13", "book": "SQLP 실전문제",
    "speakers": ["세은", "수철"],
    "problems": [{
        "problem_number": 1, "subject_area": "SQL 기본 및 활용",
        "concepts": ["JOIN", "OUTER JOIN"], "solution_summary": "요약",
        "participants": [{
            "name": "세은", "is_correct": True, "understanding": "애매",
            "concepts_covered": ["OUTER JOIN"], "concepts_missed": ["NULL 처리"],
            "errors": ["기준 테이블 방향 혼동"], "review_required": True
        }],
    }],
}

def _auth_client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_validate_ok_returns_preview():
    resp = _auth_client().post("/api/analysis/validate/", PAYLOAD, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["preview"]["problemCount"] == 1
    assert body["preview"]["participantCount"] == 2
    assert set(body["preview"]["conceptTags"]) == {"JOIN", "OUTER JOIN"}
    assert body["preview"]["sessionDate"] == "2026-06-13"
    assert body["preview"]["book"] == "SQLP 실전문제"

def test_validate_bad_understanding_fails():
    bad = {**PAYLOAD}
    bad["problems"] = [{**PAYLOAD["problems"][0]}]
    bad["problems"][0]["participants"] = [{**PAYLOAD["problems"][0]["participants"][0], "understanding": "최고"}]
    resp = _auth_client().post("/api/analysis/validate/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_validate_empty_problems_fails():
    bad = {**PAYLOAD, "problems": []}
    resp = _auth_client().post("/api/analysis/validate/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_validate_requires_auth():
    from rest_framework.test import APIClient as C
    resp = C().post("/api/analysis/validate/", PAYLOAD, format="json")
    assert resp.status_code == 401

def test_validate_duplicate_problem_number_fails():
    import copy
    bad = copy.deepcopy(PAYLOAD)
    bad["problems"].append(copy.deepcopy(PAYLOAD["problems"][0]))  # both problem_number=1
    resp = _auth_client().post("/api/analysis/validate/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_validate_duplicate_participant_name_fails():
    import copy
    bad = copy.deepcopy(PAYLOAD)
    bad["problems"][0]["participants"].append(
        copy.deepcopy(PAYLOAD["problems"][0]["participants"][0]))  # two 세은
    resp = _auth_client().post("/api/analysis/validate/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_validate_nonpositive_problem_number_fails():
    import copy
    bad = copy.deepcopy(PAYLOAD)
    bad["problems"][0]["problem_number"] = 0
    resp = _auth_client().post("/api/analysis/validate/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_validate_speaker_too_long_fails():
    import copy
    bad = copy.deepcopy(PAYLOAD)
    bad["speakers"] = ["x" * 51]
    resp = _auth_client().post("/api/analysis/validate/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_validate_problem_number_out_of_int_range_fails():
    import copy
    bad = copy.deepcopy(PAYLOAD)
    bad["problems"][0]["problem_number"] = 9999999999
    resp = _auth_client().post("/api/analysis/validate/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"
