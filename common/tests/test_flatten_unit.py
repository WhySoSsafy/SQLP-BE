from rest_framework import exceptions
from common.exceptions import _flatten, _code_for
from common import codes

def test_flatten_nested_serializer_path():
    detail = {"problems": [{"subject_area": ["허용되지 않는 과목입니다."]}]}
    out = _flatten(detail)
    assert {"path": "$.problems[0].subject_area",
            "message": "허용되지 않는 과목입니다."} in out

def test_flatten_field_scalar_list():
    out = _flatten({"email": ["This field is required."]})
    assert out == [{"path": "$.email", "message": "This field is required."}]

def test_flatten_top_level_scalar_list():
    out = _flatten(["bad"])
    assert out == [{"path": "$", "message": "bad"}]

def test_code_for_validation():
    assert _code_for(exceptions.ValidationError("x")) == codes.VALIDATION_ERROR

def test_code_for_not_found():
    assert _code_for(exceptions.NotFound()) == codes.NOT_FOUND

def test_code_for_throttled_uses_default_code():
    assert _code_for(exceptions.Throttled()) == "THROTTLED"

def test_code_for_django_http404():
    from django.http import Http404
    assert _code_for(Http404()) == codes.NOT_FOUND

def test_code_for_django_permission_denied():
    from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
    assert _code_for(DjangoPermissionDenied()) == codes.PERMISSION_DENIED

def test_unhandled_exception_enveloped_as_500():
    from common.exceptions import api_exception_handler
    resp = api_exception_handler(ValueError("boom"), {})
    assert resp.status_code == 500
    assert resp.data["ok"] is False
    assert resp.data["code"] == codes.INTERNAL_ERROR
    assert resp.data["errors"] == []
