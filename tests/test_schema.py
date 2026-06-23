import pytest
from drf_spectacular.generators import SchemaGenerator


def test_schema_generates_without_error():
    generator = SchemaGenerator()
    schema = generator.get_schema(public=True)
    assert schema is not None


def test_schema_contains_key_endpoints():
    generator = SchemaGenerator()
    schema = generator.get_schema(public=True)
    paths = schema.get("paths", {})
    assert "/api/auth/login/" in paths
    assert "/api/sessions/" in paths
    assert "/api/concepts/" in paths
    assert "/api/calendar/" in paths


def test_schema_openapi_version():
    generator = SchemaGenerator()
    schema = generator.get_schema(public=True)
    assert schema.get("openapi", "").startswith("3.")
