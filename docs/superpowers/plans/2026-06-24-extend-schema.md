# @extend_schema 전면 적용 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 모든 엔드포인트에 `@extend_schema` 데코레이터를 추가해서 Swagger UI(`/api/docs/`)에 요청 파라미터와 응답 스키마가 완전히 표시되게 한다.

**Architecture:** 앱별로 `schema_serializers.py` 신규 파일을 생성해 응답/요청 시리얼라이저를 정의하고, 각 뷰 파일에 `@extend_schema` / `@extend_schema_view` 데코레이터를 추가한다. 비즈니스 로직은 일절 변경하지 않는다.

**Tech Stack:** Django 5.0.6, djangorestframework 3.15.1, drf-spectacular 0.27.2

## Global Constraints

- 백엔드(`SQLP-BE`)만 수정. 프론트엔드(`SQLP-FE`) 미접촉.
- 브랜치: `feat/swagger-schema` (`chore/consolidate-api-docs-and-swagger`에서 분기, 머지 없음)
- 비즈니스 로직 변경 금지 — 데코레이터와 스키마 파일만 추가
- `drf-spectacular==0.27.2` (이미 설치됨)
- pytest.ini: `DJANGO_SETTINGS_MODULE = config.settings.dev`

---

## 파일 구조

| 파일 | 작업 |
|------|------|
| `accounts/schema_serializers.py` | 신규 — Login/Register/Me 응답 스키마 |
| `accounts/views.py` | 수정 — RegisterView, MeView 데코레이터 |
| `accounts/jwt.py` | 수정 — LoginView 데코레이터 |
| `study/schema_serializers.py` | 신규 — Session/WrongAnswer/Validate 스키마 |
| `study/views.py` | 수정 — 5개 뷰 데코레이터 |
| `concepts/schema_serializers.py` | 신규 — ConceptList/Detail 스키마 |
| `concepts/views.py` | 수정 — 2개 뷰 데코레이터 |
| `analytics/schema_serializers.py` | 신규 — 7개 analytics 응답 스키마 |
| `analytics/views.py` | 수정 — 7개 뷰 데코레이터 |
| `tests/test_schema_extend.py` | 신규 — 스키마 커버리지 검증 |

---

### Task 1: 브랜치 생성 + accounts 스키마

**Files:**
- Create: `accounts/schema_serializers.py`
- Modify: `accounts/views.py`
- Modify: `accounts/jwt.py`
- Create: `tests/test_schema_extend.py`

**Interfaces:**
- Produces: `LoginResponseSerializer`, `RegisterResponseSerializer`, `MeResponseSerializer`, `LoginRequestSerializer` — Task 이후 작업들이 참고할 패턴 확립

- [ ] **Step 1: 브랜치 생성**

```bash
git checkout chore/consolidate-api-docs-and-swagger
git checkout -b feat/swagger-schema
```

Expected: `Switched to a new branch 'feat/swagger-schema'`

- [ ] **Step 2: 페일링 테스트 작성**

`tests/test_schema_extend.py` 생성:

```python
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
    content = post["responses"]["200"]["content"]["application/json"]["schema"]
    assert content


def test_me_response_schema_not_empty():
    schema = get_schema()
    get = schema["paths"]["/api/users/me/"]["get"]
    content = get["responses"]["200"]["content"]["application/json"]["schema"]
    assert content
```

- [ ] **Step 3: 테스트 실행 — FAIL 확인**

```bash
pytest tests/test_schema_extend.py::test_login_response_schema_not_empty -v
```

Expected: `FAILED` — 응답 스키마가 비어서 KeyError 또는 AssertionError 발생

- [ ] **Step 4: `accounts/schema_serializers.py` 생성**

```python
from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"})


class UserInlineSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserInlineSerializer()


class RegisterResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    user = UserInlineSerializer()


class MeResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
```

- [ ] **Step 5: `accounts/jwt.py` 수정 — LoginView 데코레이터 추가**

파일 상단에 import 추가:

```python
from drf_spectacular.utils import extend_schema
from accounts.schema_serializers import LoginRequestSerializer, LoginResponseSerializer
```

`LoginView` 클래스 바로 위에 데코레이터 추가:

```python
@extend_schema(
    request=LoginRequestSerializer,
    responses={200: LoginResponseSerializer},
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
```

- [ ] **Step 6: `accounts/views.py` 수정 — RegisterView, MeView 데코레이터 추가**

파일 상단 import에 추가:

```python
from drf_spectacular.utils import extend_schema
from accounts.schema_serializers import RegisterResponseSerializer, MeResponseSerializer
```

`RegisterView` 클래스 바로 위:

```python
@extend_schema(
    responses={201: RegisterResponseSerializer},
)
class RegisterView(APIView):
    permission_classes = [AllowAny]
    ...
```

`MeView` 클래스 바로 위:

```python
@extend_schema(
    responses={200: MeResponseSerializer},
)
class MeView(APIView):
    ...
```

- [ ] **Step 7: 테스트 실행 — PASS 확인**

```bash
pytest tests/test_schema_extend.py::test_login_response_schema_not_empty tests/test_schema_extend.py::test_register_response_schema_not_empty tests/test_schema_extend.py::test_me_response_schema_not_empty -v
```

Expected: 3 passed

- [ ] **Step 8: 커밋**

```bash
git add accounts/schema_serializers.py accounts/views.py accounts/jwt.py tests/test_schema_extend.py
git commit -m "feat(accounts): add extend_schema decorators for login/register/me endpoints"
```

---

### Task 2: study 스키마

**Files:**
- Create: `study/schema_serializers.py`
- Modify: `study/views.py`
- Modify: `tests/test_schema_extend.py`

**Interfaces:**
- Produces: `SessionCreateRequestSerializer`, `SessionSummarySerializer`, `SessionDetailResponseSerializer`, `SessionCreateResponseSerializer`, `ValidateResponseSerializer`, `WrongAnswerSerializer`, `WrongAnswerUpdateRequestSerializer`, `WrongAnswerUpdateResponseSerializer`, `OkResponseSerializer`

- [ ] **Step 1: 페일링 테스트 추가**

`tests/test_schema_extend.py`에 추가:

```python
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
```

- [ ] **Step 2: 테스트 실행 — FAIL 확인**

```bash
pytest tests/test_schema_extend.py::test_sessions_post_has_request_body -v
```

Expected: `FAILED` — requestBody 없음

- [ ] **Step 3: `study/schema_serializers.py` 생성**

```python
from rest_framework import serializers


# ── 요청 스키마 ──────────────────────────────────────────────────────────────

class ParticipantInputSerializer(serializers.Serializer):
    name = serializers.CharField()
    is_correct = serializers.BooleanField()
    understanding = serializers.ChoiceField(choices=["이해", "애매", "모름"])
    concepts_covered = serializers.ListField(child=serializers.CharField())
    concepts_missed = serializers.ListField(child=serializers.CharField())
    errors = serializers.ListField(child=serializers.CharField())
    review_required = serializers.BooleanField()


class ProblemInputSerializer(serializers.Serializer):
    problem_number = serializers.IntegerField()
    subject_area = serializers.CharField()
    solution_summary = serializers.CharField()
    concepts = serializers.ListField(child=serializers.CharField())
    participants = ParticipantInputSerializer(many=True)


class SessionCreateRequestSerializer(serializers.Serializer):
    session_date = serializers.DateField()
    book = serializers.CharField()
    speakers = serializers.ListField(child=serializers.CharField())
    problems = ProblemInputSerializer(many=True)


class WrongAnswerUpdateRequestSerializer(serializers.Serializer):
    done = serializers.BooleanField()


# ── 응답 스키마 ──────────────────────────────────────────────────────────────

class OkResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()


class SessionCreateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    session_id = serializers.CharField()


class SessionSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    book = serializers.CharField()
    session_date = serializers.DateField()
    problem_count = serializers.IntegerField()
    average_understanding = serializers.FloatField()
    speakers = serializers.ListField(child=serializers.CharField())


class ParticipantDetailSerializer(serializers.Serializer):
    name = serializers.CharField()
    is_correct = serializers.BooleanField()
    understanding = serializers.CharField()
    concepts_covered = serializers.ListField(child=serializers.CharField())
    concepts_missed = serializers.ListField(child=serializers.CharField())
    errors = serializers.ListField(child=serializers.CharField())
    review_required = serializers.BooleanField()


class ProblemDetailSerializer(serializers.Serializer):
    id = serializers.CharField()
    problem_number = serializers.IntegerField()
    subject_area = serializers.CharField()
    solution_summary = serializers.CharField()
    concepts = serializers.ListField(child=serializers.CharField())
    participants = ParticipantDetailSerializer(many=True)


class SessionDetailResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    book = serializers.CharField()
    session_date = serializers.DateField()
    speakers = serializers.ListField(child=serializers.CharField())
    problems = ProblemDetailSerializer(many=True)


class ValidatePreviewSerializer(serializers.Serializer):
    sessionDate = serializers.DateField()
    book = serializers.CharField()
    problemCount = serializers.IntegerField()
    participantCount = serializers.IntegerField()
    conceptTags = serializers.ListField(child=serializers.CharField())


class ValidateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    preview = ValidatePreviewSerializer()


class WrongAnswerSerializer(serializers.Serializer):
    id = serializers.CharField()
    problem_number = serializers.IntegerField()
    book = serializers.CharField()
    session_date = serializers.DateField()
    understanding = serializers.CharField()
    review_required = serializers.BooleanField()
    done = serializers.BooleanField()


class WrongAnswerUpdateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    id = serializers.CharField()
    done = serializers.BooleanField()
```

- [ ] **Step 4: `study/views.py` 수정 — import 추가**

파일 상단 import 블록 끝에 추가:

```python
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from study.schema_serializers import (
    SessionCreateRequestSerializer,
    SessionSummarySerializer,
    SessionDetailResponseSerializer,
    SessionCreateResponseSerializer,
    ValidateResponseSerializer,
    WrongAnswerSerializer,
    WrongAnswerUpdateRequestSerializer,
    WrongAnswerUpdateResponseSerializer,
    OkResponseSerializer,
)
```

- [ ] **Step 5: `study/views.py` 수정 — ValidateView 데코레이터**

`ValidateView` 클래스 바로 위:

```python
@extend_schema(
    request=SessionCreateRequestSerializer,
    responses={200: ValidateResponseSerializer},
)
class ValidateView(APIView):
```

- [ ] **Step 6: `study/views.py` 수정 — SessionListCreateView 데코레이터**

`SessionListCreateView` 클래스 바로 위:

```python
@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter("search", str, description="책 제목 또는 참가자명 검색"),
            OpenApiParameter("understanding", str, enum=["이해", "애매", "모름"], description="이해도 필터"),
            OpenApiParameter("date_from", str, description="시작 날짜 (YYYY-MM-DD)"),
            OpenApiParameter("date_to", str, description="종료 날짜 (YYYY-MM-DD)"),
        ],
        responses={200: SessionSummarySerializer(many=True)},
    ),
    post=extend_schema(
        request=SessionCreateRequestSerializer,
        responses={201: SessionCreateResponseSerializer},
    ),
)
class SessionListCreateView(APIView):
```

- [ ] **Step 7: `study/views.py` 수정 — SessionDetailView 데코레이터**

`SessionDetailView` 클래스 바로 위:

```python
@extend_schema_view(
    get=extend_schema(responses={200: SessionDetailResponseSerializer}),
    delete=extend_schema(responses={200: OkResponseSerializer}),
)
class SessionDetailView(APIView):
```

- [ ] **Step 8: `study/views.py` 수정 — WrongAnswerListView 데코레이터**

`WrongAnswerListView` 클래스 바로 위:

```python
@extend_schema(
    responses={200: WrongAnswerSerializer(many=True)},
)
class WrongAnswerListView(APIView):
```

- [ ] **Step 9: `study/views.py` 수정 — WrongAnswerDetailView 데코레이터**

`WrongAnswerDetailView` 클래스 바로 위:

```python
@extend_schema(
    request=WrongAnswerUpdateRequestSerializer,
    responses={200: WrongAnswerUpdateResponseSerializer},
)
class WrongAnswerDetailView(APIView):
```

- [ ] **Step 10: 테스트 실행 — PASS 확인**

```bash
pytest tests/test_schema_extend.py::test_sessions_post_has_request_body tests/test_schema_extend.py::test_sessions_get_response_not_empty tests/test_schema_extend.py::test_wrong_answers_patch_has_request_body -v
```

Expected: 3 passed

- [ ] **Step 11: 커밋**

```bash
git add study/schema_serializers.py study/views.py tests/test_schema_extend.py
git commit -m "feat(study): add extend_schema decorators for session/wrong-answer/validate endpoints"
```

---

### Task 3: concepts 스키마

**Files:**
- Create: `concepts/schema_serializers.py`
- Modify: `concepts/views.py`
- Modify: `tests/test_schema_extend.py`

**Interfaces:**
- Produces: `ConceptSummarySerializer`, `ConceptDetailSerializer`

- [ ] **Step 1: 페일링 테스트 추가**

`tests/test_schema_extend.py`에 추가:

```python
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
```

- [ ] **Step 2: 테스트 실행 — FAIL 확인**

```bash
pytest tests/test_schema_extend.py::test_concept_list_response_not_empty -v
```

Expected: `FAILED`

- [ ] **Step 3: `concepts/schema_serializers.py` 생성**

```python
from rest_framework import serializers


class RelatedProblemSerializer(serializers.Serializer):
    id = serializers.CharField()
    problem_number = serializers.IntegerField()
    session_date = serializers.DateField()
    book = serializers.CharField()
    person = serializers.CharField()
    understanding = serializers.CharField()
    is_correct = serializers.BooleanField()


class ConceptSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subject = serializers.CharField()
    summary = serializers.CharField(allow_null=True)
    myUnderstanding = serializers.FloatField()
    reviewRecommended = serializers.BooleanField()


class ConceptDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subject = serializers.CharField()
    summary = serializers.CharField(allow_null=True)
    frequentQuestionTypes = serializers.ListField(child=serializers.CharField())
    confusingPoints = serializers.ListField(child=serializers.CharField())
    wrongPatterns = serializers.ListField(child=serializers.CharField())
    relatedProblems = RelatedProblemSerializer(many=True)
    myUnderstanding = serializers.FloatField()
    reviewRecommended = serializers.BooleanField()
```

- [ ] **Step 4: `concepts/views.py` 수정**

파일 상단 import 블록 끝에 추가:

```python
from drf_spectacular.utils import extend_schema
from concepts.schema_serializers import ConceptSummarySerializer, ConceptDetailSerializer
```

`ConceptListView` 바로 위:

```python
@extend_schema(responses={200: ConceptSummarySerializer(many=True)})
class ConceptListView(APIView):
```

`ConceptDetailView` 바로 위:

```python
@extend_schema(responses={200: ConceptDetailSerializer})
class ConceptDetailView(APIView):
```

- [ ] **Step 5: 테스트 실행 — PASS 확인**

```bash
pytest tests/test_schema_extend.py::test_concept_list_response_not_empty tests/test_schema_extend.py::test_concept_detail_has_related_problems -v
```

Expected: 2 passed

- [ ] **Step 6: 커밋**

```bash
git add concepts/schema_serializers.py concepts/views.py tests/test_schema_extend.py
git commit -m "feat(concepts): add extend_schema decorators for concept list/detail endpoints"
```

---

### Task 4: analytics 스키마

**Files:**
- Create: `analytics/schema_serializers.py`
- Modify: `analytics/views.py`
- Modify: `tests/test_schema_extend.py`

**Interfaces:**
- Produces: `WeakConceptSerializer`, `RecommendationSerializer`, `DashboardResponseSerializer`, `CalendarResponseSerializer`, `StudyComparisonResponseSerializer`, `GrowthReportResponseSerializer`, `ProblemAnalysisSchemaSerializer`, `ProblemAnalysisCreateResponseSerializer`
- Note: `analytics/views.py`에는 이미 `ProblemAnalysisItemSerializer`가 `analytics.serializers`에서 임포트됨 — analytics/schema_serializers.py에는 중복 생성하지 않고 기존 것 활용

- [ ] **Step 1: 페일링 테스트 추가**

`tests/test_schema_extend.py`에 추가:

```python
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
```

- [ ] **Step 2: 테스트 실행 — FAIL 확인**

```bash
pytest tests/test_schema_extend.py::test_calendar_has_year_month_params -v
```

Expected: `FAILED` — parameters 없음

- [ ] **Step 3: `analytics/schema_serializers.py` 생성**

```python
from rest_framework import serializers


# ── WeakConcepts ─────────────────────────────────────────────────────────────

class WeakConceptSerializer(serializers.Serializer):
    name = serializers.CharField()
    subject = serializers.CharField()
    totalProblems = serializers.IntegerField()
    weakCountByParticipant = serializers.DictField(child=serializers.IntegerField())
    scoreByParticipant = serializers.DictField(child=serializers.FloatField())
    averageScore = serializers.FloatField()
    lastReviewDate = serializers.DateField(allow_null=True)
    recommend = serializers.BooleanField()


# ── Recommendations ───────────────────────────────────────────────────────────

class RecommendationSerializer(serializers.Serializer):
    concept = serializers.CharField()
    subject = serializers.CharField()
    reason = serializers.CharField()
    score = serializers.FloatField()


# ── Dashboard ─────────────────────────────────────────────────────────────────

class RecentSessionSerializer(serializers.Serializer):
    id = serializers.CharField()
    date = serializers.DateField()
    book = serializers.CharField()
    problemCount = serializers.IntegerField()
    averageUnderstanding = serializers.FloatField()


class DashboardResponseSerializer(serializers.Serializer):
    weeklyProblemCount = serializers.IntegerField()
    reviewRequiredCount = serializers.IntegerField()
    averageUnderstanding = serializers.FloatField()
    studyStreak = serializers.IntegerField()
    recommendations = RecommendationSerializer(many=True)
    recentSessions = RecentSessionSerializer(many=True)


# ── Calendar ──────────────────────────────────────────────────────────────────

class CalendarDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    problemCount = serializers.IntegerField()
    averageUnderstanding = serializers.FloatField()
    mainConcepts = serializers.ListField(child=serializers.CharField())
    reviewRequiredCount = serializers.IntegerField()


class CalendarResponseSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    days = CalendarDaySerializer(many=True)
    weeklyProblemCount = serializers.IntegerField()
    monthlyProblemCount = serializers.IntegerField()
    studyStreak = serializers.IntegerField()


# ── StudyComparison ───────────────────────────────────────────────────────────

class ComparisonParticipantSerializer(serializers.Serializer):
    name = serializers.CharField()
    averageUnderstanding = serializers.FloatField()
    correctCount = serializers.IntegerField()
    reviewRequiredCount = serializers.IntegerField()
    weakConcepts = serializers.ListField(child=serializers.CharField())


class ComparisonProblemParticipantSerializer(serializers.Serializer):
    name = serializers.CharField()
    isCorrect = serializers.BooleanField()
    understanding = serializers.CharField()
    reviewRequired = serializers.BooleanField()


class ComparisonProblemSerializer(serializers.Serializer):
    problemNumber = serializers.IntegerField()
    concepts = serializers.ListField(child=serializers.CharField())
    participants = ComparisonProblemParticipantSerializer(many=True)


class StudyComparisonResponseSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    book = serializers.CharField()
    sessionDate = serializers.DateField()
    participants = ComparisonParticipantSerializer(many=True)
    problems = ComparisonProblemSerializer(many=True)


# ── GrowthReport ──────────────────────────────────────────────────────────────

class TrendItemSerializer(serializers.Serializer):
    date = serializers.DateField()
    averageUnderstanding = serializers.FloatField()


class GrowthReportResponseSerializer(serializers.Serializer):
    period = serializers.CharField()
    problemCount = serializers.IntegerField()
    averageUnderstanding = serializers.FloatField()
    reviewRequiredCount = serializers.IntegerField()
    improvedConcepts = serializers.ListField(child=serializers.CharField())
    stillWeakConcepts = serializers.ListField(child=serializers.CharField())
    trend = TrendItemSerializer(many=True)


# ── ProblemAnalysis ───────────────────────────────────────────────────────────

class ProblemAnalysisRequestSerializer(serializers.Serializer):
    book = serializers.CharField()
    problems = serializers.ListField(
        child=serializers.DictField(),
        help_text="각 문제: {problem_number, answer, understanding, review_required}"
    )


class ProblemAnalysisCreateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    created_count = serializers.IntegerField()
```

- [ ] **Step 4: `analytics/views.py` 수정 — import 추가**

파일 상단 import 블록 끝에 추가:

```python
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from analytics.schema_serializers import (
    WeakConceptSerializer,
    RecommendationSerializer,
    DashboardResponseSerializer,
    CalendarResponseSerializer,
    StudyComparisonResponseSerializer,
    GrowthReportResponseSerializer,
    ProblemAnalysisRequestSerializer,
    ProblemAnalysisCreateResponseSerializer,
)
```

- [ ] **Step 5: `analytics/views.py` 수정 — 각 뷰 데코레이터 추가**

`WeakConceptsView` 바로 위:

```python
@extend_schema(responses={200: WeakConceptSerializer(many=True)})
class WeakConceptsView(APIView):
```

`ReviewRecommendationsView` 바로 위:

```python
@extend_schema(responses={200: RecommendationSerializer(many=True)})
class ReviewRecommendationsView(APIView):
```

`DashboardSummaryView` 바로 위:

```python
@extend_schema(responses={200: DashboardResponseSerializer})
class DashboardSummaryView(APIView):
```

`CalendarView` 바로 위:

```python
@extend_schema(
    parameters=[
        OpenApiParameter("year", int, required=True, description="조회 연도 (예: 2026)"),
        OpenApiParameter("month", int, required=True, description="조회 월 (1-12)"),
    ],
    responses={200: CalendarResponseSerializer},
)
class CalendarView(APIView):
```

`StudyComparisonView` 바로 위:

```python
@extend_schema(
    parameters=[
        OpenApiParameter("session_id", str, required=True, description="비교할 세션 ID"),
    ],
    responses={200: StudyComparisonResponseSerializer},
)
class StudyComparisonView(APIView):
```

`ProblemAnalysisView` 바로 위:

```python
@extend_schema_view(
    get=extend_schema(responses={200: ProblemAnalysisItemSerializer(many=True)}),
    post=extend_schema(
        request=ProblemAnalysisRequestSerializer,
        responses={201: ProblemAnalysisCreateResponseSerializer},
    ),
)
class ProblemAnalysisView(APIView):
```

`GrowthReportView` 바로 위:

```python
@extend_schema(
    parameters=[
        OpenApiParameter("period", str, default="monthly", description="기간 (현재 echo-only, 항상 전체 기간 반환)"),
    ],
    responses={200: GrowthReportResponseSerializer},
)
class GrowthReportView(APIView):
```

- [ ] **Step 6: 테스트 실행 — PASS 확인**

```bash
pytest tests/test_schema_extend.py -v
```

Expected: 모든 테스트 통과 (기존 3개 + 신규 4개 = 최소 7개)

- [ ] **Step 7: spectacular validate 실행**

```bash
python manage.py spectacular --validate
```

Expected: 오류 없이 종료 (WARNING은 무시 가능)

- [ ] **Step 8: 커밋**

```bash
git add analytics/schema_serializers.py analytics/views.py tests/test_schema_extend.py
git commit -m "feat(analytics): add extend_schema decorators for all analytics endpoints"
```

---

### Task 5: 최종 검증 + Push + PR

**Files:**
- No new files

- [ ] **Step 1: 전체 테스트 실행**

```bash
pytest tests/ -v
```

Expected: 모든 테스트 통과

- [ ] **Step 2: 스키마 전체 검증**

```bash
python manage.py spectacular --validate
```

Expected: 오류 없이 종료

- [ ] **Step 3: 브랜치 push**

```bash
git push -u origin feat/swagger-schema
```

- [ ] **Step 4: PR 생성**

```bash
gh pr create \
  --base chore/consolidate-api-docs-and-swagger \
  --head feat/swagger-schema \
  --title "feat: add @extend_schema to all 20 endpoints for complete Swagger UI" \
  --body "## Summary
- 20개 엔드포인트 전체에 @extend_schema 데코레이터 추가
- 앱별 schema_serializers.py 4개 신규 생성
- Swagger UI /api/docs/ 에서 요청 파라미터 및 응답 스키마 완전 표시
- 비즈니스 로직 변경 없음

## Test plan
- [x] pytest tests/ 전체 통과
- [x] python manage.py spectacular --validate 오류 없음
- [ ] 브라우저 /api/docs/ 에서 각 엔드포인트 파라미터/응답 시각 확인"
```

- [ ] **Step 5: main으로 복귀**

```bash
git checkout main
```
