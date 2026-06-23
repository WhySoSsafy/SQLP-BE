# Swagger/OpenAPI 설정 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `drf-spectacular`을 설치하고 `/api/docs/` (Swagger UI), `/api/redoc/` (ReDoc), `/api/schema/` (raw JSON)를 `DEBUG=True` 환경에서 서빙한다.

**Architecture:** drf-spectacular이 DRF 뷰/시리얼라이저를 정적 분석해서 OpenAPI 3.0 JSON 스키마를 자동 생성. Swagger UI는 그 스키마를 브라우저에서 렌더링. `DEBUG=True`일 때만 URL이 라우팅에 포함되어 prod 환경에서는 404.

**Tech Stack:** Django 5.0.6, djangorestframework 3.15.1, drf-spectacular 0.27.2, pytest-django 4.8.0

## Global Constraints

- 백엔드(`SQLP-BE`)만 수정. 프론트엔드(`SQLP-FE`) 미접촉.
- 브랜치: `docs/swagger-setup` (`main`에서 분기, 머지 없음)
- `DEBUG=True` 환경(dev + staging)에서만 schema URL 노출. prod(`DEBUG=False`) 제외.
- `drf-spectacular==0.27.2` 고정 버전 사용.
- pytest.ini 기준: `DJANGO_SETTINGS_MODULE = config.settings.dev`

---

## 파일 구조

| 파일 | 작업 | 내용 |
|------|------|------|
| `requirements.txt` | 수정 | `drf-spectacular==0.27.2` 추가 |
| `config/settings/base.py` | 수정 | INSTALLED_APPS, REST_FRAMEWORK, SPECTACULAR_SETTINGS 수정 |
| `config/urls.py` | 수정 | `DEBUG` 기준 조건부 schema URL 3개 추가 |
| `tests/test_schema.py` | 생성 | 스키마 자동 생성 검증 테스트 |

---

### Task 1: drf-spectacular 설치 및 Django 설정

**Files:**
- Modify: `requirements.txt`
- Modify: `config/settings/base.py`
- Create: `tests/test_schema.py`

**Interfaces:**
- Produces: `SPECTACULAR_SETTINGS` dict, `"drf_spectacular"` in INSTALLED_APPS, `AutoSchema` as DEFAULT_SCHEMA_CLASS — Task 2에서 URL을 추가할 때 이 설정이 전제됨.

- [ ] **Step 1: `docs/swagger-setup` 브랜치 생성**

```bash
git checkout -b docs/swagger-setup
```

Expected: `Switched to a new branch 'docs/swagger-setup'`

- [ ] **Step 2: 페일링 테스트 작성**

`tests/test_schema.py` 생성 (디렉터리가 없으면 `tests/` 폴더 먼저 생성):

```python
import pytest
from drf_spectacular.generators import SchemaGenerator


def test_schema_generates_without_error():
    generator = SchemaGenerator()
    schema = generator.get_schema()
    assert schema is not None


def test_schema_contains_key_endpoints():
    generator = SchemaGenerator()
    schema = generator.get_schema()
    paths = schema.get("paths", {})
    assert "/api/auth/login/" in paths
    assert "/api/sessions/" in paths
    assert "/api/concepts/" in paths
    assert "/api/calendar/" in paths


def test_schema_openapi_version():
    generator = SchemaGenerator()
    schema = generator.get_schema()
    assert schema.get("openapi", "").startswith("3.")
```

- [ ] **Step 3: 테스트 실행 — FAIL 확인**

```bash
pytest tests/test_schema.py -v
```

Expected: `ModuleNotFoundError: No module named 'drf_spectacular'` — drf-spectacular 미설치 상태라 실패해야 함.

- [ ] **Step 4: requirements.txt에 drf-spectacular 추가**

`requirements.txt` 전체 내용으로 교체:

```
Django==5.0.6
djangorestframework==3.15.1
djangorestframework-simplejwt==5.3.1
psycopg[binary]==3.1.19
django-environ==0.11.2
drf-spectacular==0.27.2
pytest==8.2.0
pytest-django==4.8.0
factory_boy==3.3.0
```

- [ ] **Step 5: 패키지 설치**

```bash
pip install drf-spectacular==0.27.2
```

Expected: `Successfully installed drf-spectacular-0.27.2 ...`

- [ ] **Step 6: INSTALLED_APPS에 drf_spectacular 추가**

`config/settings/base.py`의 INSTALLED_APPS를 아래로 교체 (`"rest_framework"` 바로 아래에 삽입):

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "accounts",
    "study",
    "concepts",
    "analytics",
    "common",
]
```

- [ ] **Step 7: REST_FRAMEWORK에 DEFAULT_SCHEMA_CLASS 추가**

`config/settings/base.py`의 REST_FRAMEWORK 딕셔너리를 아래로 교체:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
```

- [ ] **Step 8: SPECTACULAR_SETTINGS 블록 추가**

`config/settings/base.py` 파일 끝 (`IMPROVED_THRESHOLD = 70` 아래)에 추가:

```python
SPECTACULAR_SETTINGS = {
    "TITLE": "SQLP API",
    "DESCRIPTION": "SQLP 스터디 세션 관리 백엔드 API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
```

- [ ] **Step 9: Django 설정 점검**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 10: 테스트 실행 — PASS 확인**

```bash
pytest tests/test_schema.py -v
```

Expected:
```
PASSED tests/test_schema.py::test_schema_generates_without_error
PASSED tests/test_schema.py::test_schema_contains_key_endpoints
PASSED tests/test_schema.py::test_schema_openapi_version
```

`test_schema_contains_key_endpoints`가 실패하면 — `schema.get("paths", {})` 내용을 출력해서 실제 path 키 형식 확인 후 테스트 경로 문자열 수정.

- [ ] **Step 11: 커밋**

```bash
git add requirements.txt config/settings/base.py tests/test_schema.py
git commit -m "feat: install drf-spectacular and configure OpenAPI schema generation"
```

---

### Task 2: 스키마 URL 라우팅 추가 및 최종 검증

**Files:**
- Modify: `config/urls.py`

**Interfaces:**
- Consumes: `SPECTACULAR_SETTINGS`, `"drf_spectacular"` in INSTALLED_APPS (Task 1 완료 전제)
- Produces: `GET /api/schema/` (name=`"schema"`), `GET /api/docs/` (name=`"swagger-ui"`), `GET /api/redoc/` (name=`"redoc"`) — `DEBUG=True`일 때만 활성화

- [ ] **Step 1: config/urls.py를 아래 내용으로 교체**

```python
from django.contrib import admin
from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("accounts.urls")),
    path("api/", include("study.urls")),
    path("api/", include("concepts.urls")),
    path("api/", include("analytics.urls")),
]

if settings.DEBUG:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularSwaggerView,
        SpectacularRedocView,
    )
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]
```

- [ ] **Step 2: 스키마 유효성 검사**

```bash
python manage.py spectacular --validate
```

Expected: 오류 없이 종료. 경고(WARNING)는 무시 가능. `Error` 출력 시 해당 뷰에서 직접 `dict` 반환하는지 확인 — 이번 범위에서는 수정하지 않고 넘어감.

- [ ] **Step 3: prod 환경에서 URL 미노출 확인**

```bash
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'
import django
django.setup()
from django.urls import reverse
try:
    reverse('schema')
    print('ERROR: schema URL exists in prod')
except Exception:
    print('OK: schema URL not in prod')
"
```

Expected: `OK: schema URL not in prod`

- [ ] **Step 4: 로컬 서버 기동 및 Swagger UI 브라우저 확인**

```bash
python manage.py runserver
```

브라우저에서 다음 3개 URL 확인:
- `http://127.0.0.1:8000/api/schema/` → JSON 응답 (openapi: 3.x.x 키 포함)
- `http://127.0.0.1:8000/api/docs/` → Swagger UI 렌더링, 엔드포인트 목록 표시
- `http://127.0.0.1:8000/api/redoc/` → ReDoc 렌더링

- [ ] **Step 5: 커밋**

```bash
git add config/urls.py
git commit -m "feat: add swagger ui and redoc urls under DEBUG flag"
```

- [ ] **Step 6: main으로 복귀**

```bash
git checkout main
```
