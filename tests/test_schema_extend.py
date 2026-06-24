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
