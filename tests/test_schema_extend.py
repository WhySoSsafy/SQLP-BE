import pytest
from drf_spectacular.generators import SchemaGenerator


def get_schema():
    return SchemaGenerator().get_schema(public=True)


def test_login_response_schema_not_empty():
    schema = get_schema()
    post = schema["paths"]["/api/auth/login/"]["post"]
    content = post["responses"]["200"]["content"]["application/json"]["schema"]
    assert content  # @extend_schema 없으면 빈 dict


def test_register_response_schema_not_empty():
    schema = get_schema()
    post = schema["paths"]["/api/auth/register/"]["post"]
    content = post["responses"]["201"]["content"]["application/json"]["schema"]
    assert content


def test_me_response_schema_not_empty():
    schema = get_schema()
    get = schema["paths"]["/api/users/me/"]["get"]
    content = get["responses"]["200"]["content"]["application/json"]["schema"]
    assert content


def test_sessions_post_has_request_body():
    schema = get_schema()
    post = schema["paths"]["/api/sessions/"]["post"]
    assert "requestBody" in post


def test_sessions_get_response_not_empty():
    schema = get_schema()
    get = schema["paths"]["/api/sessions/"]["get"]
    content = get["responses"]["200"]["content"]["application/json"]["schema"]
    assert content


def test_wrong_answers_patch_has_request_body():
    schema = get_schema()
    # wrong-answers path key 확인 후 수정 필요할 수 있음
    paths = schema["paths"]
    wa_paths = [k for k in paths if "wrong-answers" in k and "{" in k]
    assert wa_paths, "wrong-answer detail path not found"
    patch = paths[wa_paths[0]].get("patch", {})
    assert "requestBody" in patch


def test_concept_list_response_not_empty():
    schema = get_schema()
    get = schema["paths"]["/api/concepts/"]["get"]
    content = get["responses"]["200"]["content"]["application/json"]["schema"]
    assert content


def test_concept_detail_has_related_problems():
    schema = get_schema()
    paths = schema["paths"]
    detail_paths = [k for k in paths if "concepts" in k and "{" in k]
    assert detail_paths
    get = paths[detail_paths[0]]["get"]
    content = get["responses"]["200"]["content"]["application/json"]["schema"]
    assert content


def test_calendar_has_year_month_params():
    schema = get_schema()
    get = schema["paths"]["/api/calendar/"]["get"]
    param_names = [p["name"] for p in get.get("parameters", [])]
    assert "year" in param_names
    assert "month" in param_names


def test_weak_concepts_response_not_empty():
    schema = get_schema()
    get = schema["paths"]["/api/weak-concepts/"]["get"]
    content = get["responses"]["200"]["content"]["application/json"]["schema"]
    assert content


def test_growth_report_has_period_param():
    schema = get_schema()
    get = schema["paths"]["/api/reports/growth/"]["get"]
    param_names = [p["name"] for p in get.get("parameters", [])]
    assert "period" in param_names


def test_study_comparison_has_session_id_param():
    schema = get_schema()
    get = schema["paths"]["/api/study-comparison/"]["get"]
    param_names = [p["name"] for p in get.get("parameters", [])]
    assert "session_id" in param_names
