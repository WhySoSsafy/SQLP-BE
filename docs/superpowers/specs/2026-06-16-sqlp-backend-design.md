# SQLP 스터디 학습 추적 백엔드 설계

작성일: 2026-06-16
원본 API 명세: `api.md` (엔드포인트 20개)

## 1. 개요

SQLP 자격증 스터디 그룹의 학습 세션을 기록하고, 이해도/취약개념/복습추천/성장리포트 등
파생 분석을 제공하는 REST 백엔드. Django + DRF로 구현한다.

### 확정 전제
- 스택: **Django 5 + Django REST Framework**
- 인증: **JWT** (`djangorestframework-simplejwt`, access/refresh)
- DB: **PostgreSQL** (ArrayField 사용, 개념은 정규화 테이블)
- 데이터 범위: **그룹 단위 공유**. 단일 기본 그룹 + 회원가입 시 자동 소속(그룹 관리 API는 범위 외)
- 이해도 점수: **3단계(모름/애매/이해 = 0/50/100) + is_correct 가중**
- 분석 계산 방식: **관계형 모델 + 요청 시 실시간 ORM 집계** (서비스 레이어로 격리)

### 비범위 (YAGNI)
- 그룹 생성/초대/멤버 관리 API
- 사전계산 스냅샷/캐싱 (현 규모에선 불필요)
- 토큰 블랙리스트/로그아웃 (기본 SimpleJWT만)

## 2. 프로젝트 구조

```
config/
  settings/   # base.py, dev.py, prod.py (django-environ, .env)
  urls.py
accounts/     # User, StudyGroup, auth/register/me
study/        # StudySession, Problem, ProblemParticipant
  services/   # session_create.py, slug.py, scoring.py
concepts/     # Concept (개념 요약)
analytics/    # ProblemAnalysis + 대시보드/취약개념/추천/캘린더/비교/리포트 뷰
  services/   # analytics.py
common/       # 공통 exception handler, 응답 포맷, 코드 상수
```

뷰는 얇게 유지하고 계산 로직은 모두 `services/`에 둔다.

## 3. 데이터 모델

### accounts
- **StudyGroup**: `name`, `slug`. 마이그레이션으로 기본 그룹 1개 생성.
- **User** (커스텀, 이메일 로그인): `email`(unique, USERNAME_FIELD), `name`, `password`,
  `profile_label`(기본 `""`), `group`(FK → StudyGroup, 가입 시 기본 그룹 자동 배정).

### study
- **StudySession**: `id`(CharField PK, 슬러그), `group`(FK), `session_date`, `book`, `created_at`.
  - 슬러그 규칙: `{date}-{book슬러그}-{문제번호들}`, 충돌 시 `-2`, `-3` … 접미사.
    예) `2026-06-13-sqlp-실전문제-1-2`.
  - `speakers`는 참가자에서 파생(저장 안 함).
- **Problem**: `id`(CharField PK = `{session_id}-p{n}`), `session`(FK), `problem_number`,
  `subject_area`, `solution_summary`, `concepts`(M2M → Concept, 이름으로 get_or_create).
- **ProblemParticipant**: `problem`(FK), `name`, `member`(FK→User, nullable; 그룹 내 이름 매칭 시 연결),
  `is_correct`, `understanding`(choices: `모름`/`애매`/`이해`),
  `concepts_covered`/`concepts_missed`/`errors`(ArrayField of str),
  `review_required`, **`done`**(오답노트 복습완료 플래그, 기본 False).
  - 오답노트 id = `{problem_id}-{name}` (엔드포인트 12·13).

### concepts
- **Concept**: `id`(int PK), `group`(FK), `name`, `subject`, `summary`,
  `frequent_question_types`/`confusing_points`/`wrong_patterns`(ArrayField of str).
  `(group, name)` unique.

### analytics
- **ProblemAnalysis**: `id`(int PK), `group`(FK), `book`, `problem_number`, `subject_area`,
  `concepts`(ArrayField of names), `estimated_difficulty`(`상`/`중`/`하`), `frequency`, `priority`.
  세션과 무관한 난이도/주제 카탈로그.

### 참가자↔유저 관계
API 계약은 이름 문자열을 그대로 유지한다. 그룹 내 같은 이름 멤버가 있으면 `member` FK로 연결,
없으면 이름만 보관한다. 모든 데이터 쿼리는 `request.user.group` 기준으로 스코핑한다.

## 4. 엔드포인트 매핑

| # | 메서드/경로 | 처리 |
|---|---|---|
| 1 | POST `/api/auth/login/` | SimpleJWT 커스텀 (access/refresh/user 반환) |
| 2 | POST `/api/auth/register/` | 유저 생성 + 기본 그룹 배정 |
| 3 | GET `/api/users/me/` | 인증 유저 직렬화 |
| 4 | POST `/api/analysis/validate/` | 입력 JSON 검증만, 저장 없음, `preview` 반환 |
| 5 | POST `/api/sessions/` | 세션+문제+참가자 생성, 슬러그 발급, 중복 → `DUPLICATE_SESSION` |
| 6 | GET `/api/sessions/` | 목록 + `search`/`understanding`/`date_from`/`date_to` 필터, 파생 집계 |
| 7 | GET `/api/sessions/{id}/` | 상세(문제·참가자 중첩) |
| 8 | DELETE `/api/sessions/{id}/` | 삭제 |
| 9 | GET `/api/dashboard/summary/` | 주간문제수·복습필요·평균이해도·streak·추천·최근세션 |
| 10 | GET `/api/recommendations/review/` | 복습 추천(점수 낮은 개념) |
| 11 | GET `/api/weak-concepts/` | 개념별·참가자별 집계 |
| 12 | GET `/api/wrong-answers/` | review_required 또는 오답인 참가자 행 |
| 13 | PATCH `/api/wrong-answers/{id}/` | `done` 토글 |
| 14 | GET `/api/calendar/` | `year`/`month` 일별 집계 |
| 15 | GET `/api/study-comparison/` | `session_id` 참가자 비교 |
| 16 | GET `/api/concepts/` | 개념 목록 + `myUnderstanding` |
| 17 | GET `/api/concepts/{id}/` | 개념 상세 + 관련 문제 |
| 18 | POST `/api/problem-analysis/` | 난이도/주제 분석 일괄 등록 (`created_count`) |
| 19 | GET `/api/problem-analysis/` | 분석 목록 |
| 20 | GET `/api/reports/growth/` | `period`(monthly 등) 성장 리포트 |

편의용 추가: POST `/api/auth/refresh/` (SimpleJWT 기본 토큰 갱신, 스펙 외).

## 5. 점수/분석 로직 (`study/services/scoring.py`)

`settings`에 노출하여 조정 가능한 상수:
- `UNDERSTANDING_SCORE = {"모름": 0, "애매": 50, "이해": 100}`
- 참가자 점수: `score = round(base*0.7 + (100 if is_correct else 0)*0.3)` → 0~100
- `averageUnderstanding` = 대상 범위 참가자 점수 평균(반올림)
- 취약개념 점수 = 해당 개념 관련 참가자 점수 평균(낮을수록 취약)
- `recommend` / `reviewRecommended` = 점수 < 50
- 복습추천 `score` = 100 − 취약점수, 내림차순 정렬 후 상위 N
- `studyStreak` = 오늘부터 역순 연속 학습일 수

> 참고: `api.md` 응답 본문의 숫자(50/60/40 등)는 목 데이터이며, 위 공식이 구현 기준이다.
> 실제 출력값은 공식 결과를 따른다.

## 6. 인증 & 그룹

- `IsAuthenticated` 기본 권한, `login`/`register`만 공개.
- `Authorization: Bearer <access>` 헤더.
- 회원가입 시 단일 기본 그룹 자동 소속.

## 7. 에러 처리

커스텀 DRF exception handler가 모든 에러를 공통 형식으로 변환:

```json
{
  "ok": false,
  "code": "VALIDATION_ERROR",
  "message": "입력값이 올바르지 않습니다.",
  "errors": [{ "path": "$.problems[0].subject_area", "message": "허용되지 않는 과목입니다." }]
}
```

코드 상수: `VALIDATION_ERROR`, `DUPLICATE_SESSION`, `NOT_FOUND`, `AUTHENTICATION_FAILED`.
검증 실패 시 `errors[].path`는 JSONPath 형태(`$.problems[0].field`)로 생성한다.

## 8. 테스트

- pytest + pytest-django, factory_boy.
- 엔드포인트별 통합 테스트(인증/스코핑 포함) + 서비스 단위 테스트(점수 공식, 슬러그 생성,
  중복 감지, 그룹 스코핑).
- 구현은 TDD로 진행한다.

## 9. 의존성

Django 5, djangorestframework, djangorestframework-simplejwt, psycopg(3),
django-environ, pytest-django, factory_boy.
