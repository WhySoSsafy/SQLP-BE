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
