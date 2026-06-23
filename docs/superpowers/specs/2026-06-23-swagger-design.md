# Swagger/OpenAPI 문서 설정 설계

**작성일:** 2026-06-23  
**범위:** 백엔드(SQLP-BE)만 수정. 프론트엔드(SQLP-FE) 미접촉.

---

## 목표

프론트엔드 팀(현재 React → Vue 전환 예정)이 `/api/docs/` URL 하나로 전체 API를 브라우저에서 바로 확인하고 테스트할 수 있게 한다.

---

## 결정 사항

| 항목 | 결정 |
|------|------|
| 라이브러리 | `drf-spectacular` (OpenAPI 3.0, Django 5.x 공식 지원) |
| 스키마 생성 방식 | 코드에서 자동 생성 (DRF 뷰/시리얼라이저 정적 분석) |
| 접근 제한 | 없음 (URL 알면 누구나 접근) |
| 노출 환경 | `DEBUG=True` 환경만 (dev + staging). prod(`DEBUG=False`) 제외 |

---

## 제공 URL

```
GET /api/schema/       → OpenAPI 3.0 JSON 스키마 (raw)
GET /api/docs/         → Swagger UI (브라우저 인터랙티브)
GET /api/redoc/        → ReDoc UI (대안 뷰어)
```

---

## 변경 파일

### 1. `requirements.txt`

```
drf-spectacular==0.27.2
```

### 2. `config/settings/base.py`

`INSTALLED_APPS`에 `"drf_spectacular"` 추가.

`SPECTACULAR_SETTINGS` 블록 추가:

```python
SPECTACULAR_SETTINGS = {
    "TITLE": "SQLP API",
    "DESCRIPTION": "SQLP 스터디 세션 관리 백엔드 API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
```

`REST_FRAMEWORK`의 `DEFAULT_SCHEMA_CLASS` 설정:

```python
REST_FRAMEWORK = {
    ...
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
```

### 3. `config/urls.py`

`DEBUG` 기준 조건부 URL 포함:

```python
from django.conf import settings

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

---

## 스키마 커버리지 예상

| 엔드포인트 수 | 자동 커버 | 수동 보완 필요 |
|---|---|---|
| 18개 전체 | 시리얼라이저 기반 뷰 (대부분) | 직접 `dict` 반환 뷰 (응답 스키마 비어있음) |

drf-spectacular이 자동으로 추출하는 정보:
- 시리얼라이저 필드 (요청/응답 바디)
- JWT 인증 헤더 (`Authorization: Bearer ...`)
- 쿼리파라미터 (DRF FilterBackend 연동 시)
- HTTP 메서드, URL 패턴

현재 일부 뷰는 직접 `dict`를 반환하므로 응답 스키마가 `{}` 로 표시될 수 있음. 향후 `@extend_schema(responses=...)` decorator로 보완 가능 — 이번 범위에서는 제외.

---

## 미포함 사항 (향후 작업)

- `@extend_schema` decorator로 개별 뷰 응답 스키마 보완
- Staging 전용 settings 파일 (`config/settings/staging.py`) 추가
- 인증 토큰 입력 버튼 (`SECURITY` 설정) — drf-spectacular 기본 제공이므로 설정만 추가하면 됨

---

## 브랜치 전략

단일 브랜치: `docs/swagger-setup`  
`main`에서 분기 → 작업 → 커밋 → `main` 복귀 (머지 없음)
