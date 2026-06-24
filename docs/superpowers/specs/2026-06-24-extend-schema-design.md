# @extend_schema 전면 적용 설계

**작성일:** 2026-06-24
**범위:** 백엔드(SQLP-BE)만 수정. 프론트엔드(SQLP-FE) 미접촉.

---

## 목표

Swagger UI(`/api/docs/`)에서 모든 엔드포인트의 요청 파라미터와 응답 스키마가 상세히 표시되도록 한다.

---

## 결정 사항

| 항목 | 결정 |
|------|------|
| 스키마 정의 위치 | 앱별 `schema_serializers.py` 신규 파일 |
| 뷰 수정 방식 | `@extend_schema` 데코레이터 추가 |
| 동적 키 응답 | `DictField(child=...)` 처리 |
| 브랜치 베이스 | `chore/consolidate-api-docs-and-swagger` |
| 신규 브랜치 | `feat/swagger-schema` |

---

## 파일 구조

### 신규 생성 (4개)
- `accounts/schema_serializers.py`
- `study/schema_serializers.py`
- `concepts/schema_serializers.py`
- `analytics/schema_serializers.py`

### 수정 (5개)
- `accounts/views.py` — RegisterView, MeView
- `accounts/jwt.py` — LoginView
- `study/views.py` — ValidateView, SessionListCreateView, SessionDetailView, WrongAnswerListView, WrongAnswerDetailView
- `concepts/views.py` — ConceptListView, ConceptDetailView
- `analytics/views.py` — WeakConceptsView, ReviewRecommendationsView, DashboardSummaryView, CalendarView, StudyComparisonView, ProblemAnalysisView, GrowthReportView

---

## 앱별 스키마 정의

### accounts/schema_serializers.py

```python
from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()

class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

class RegisterResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    user = UserSerializer()

class MeResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
```

### study/schema_serializers.py

```python
from rest_framework import serializers

# 요청 스키마
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

# 응답 스키마
class SessionSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    book = serializers.CharField()
    session_date = serializers.DateField()
    problem_count = serializers.IntegerField()
    average_understanding = serializers.FloatField()
    speakers = serializers.ListField(child=serializers.CharField())

class SessionCreateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    session_id = serializers.CharField()

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

class OkResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()

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

class WrongAnswerUpdateRequestSerializer(serializers.Serializer):
    done = serializers.BooleanField()

class WrongAnswerUpdateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    id = serializers.CharField()
    done = serializers.BooleanField()
```

### concepts/schema_serializers.py

```python
from rest_framework import serializers

class ConceptSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subject = serializers.CharField()
    summary = serializers.CharField(allow_null=True)
    myUnderstanding = serializers.FloatField()
    reviewRecommended = serializers.BooleanField()

class RelatedProblemSerializer(serializers.Serializer):
    id = serializers.CharField()
    problem_number = serializers.IntegerField()
    session_date = serializers.DateField()
    book = serializers.CharField()
    person = serializers.CharField()
    understanding = serializers.CharField()
    is_correct = serializers.BooleanField()

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

### analytics/schema_serializers.py

```python
from rest_framework import serializers

# WeakConcepts
class WeakConceptSerializer(serializers.Serializer):
    name = serializers.CharField()
    subject = serializers.CharField()
    totalProblems = serializers.IntegerField()
    weakCountByParticipant = serializers.DictField(child=serializers.IntegerField())
    scoreByParticipant = serializers.DictField(child=serializers.FloatField())
    averageScore = serializers.FloatField()
    lastReviewDate = serializers.DateField(allow_null=True)
    recommend = serializers.BooleanField()

# ReviewRecommendations
class RecommendationSerializer(serializers.Serializer):
    concept = serializers.CharField()
    subject = serializers.CharField()
    reason = serializers.CharField()
    score = serializers.FloatField()

# Dashboard
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

# Calendar
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

# StudyComparison
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

# GrowthReport
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

# ProblemAnalysis
class ProblemAnalysisItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    book = serializers.CharField()
    problem_number = serializers.IntegerField()
    answer = serializers.CharField(allow_null=True)
    understanding = serializers.CharField()
    review_required = serializers.BooleanField()

class ProblemAnalysisRequestSerializer(serializers.Serializer):
    book = serializers.CharField()
    problems = serializers.ListField(child=serializers.DictField())

class ProblemAnalysisCreateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    created_count = serializers.IntegerField()
```

---

## 데코레이터 패턴

### 클래스 기반 뷰 — `@extend_schema_view`
```python
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

@extend_schema_view(
    get=extend_schema(
        parameters=[OpenApiParameter("year", int, required=True),
                    OpenApiParameter("month", int, required=True)],
        responses={200: CalendarResponseSerializer}
    )
)
class CalendarView(APIView):
    ...
```

### 단일 메서드 — `@extend_schema`
```python
@extend_schema(request=LoginSerializer, responses={200: LoginResponseSerializer})
class LoginView(TokenObtainPairView):
    ...
```

---

## 커버리지

| 앱 | 엔드포인트 | 요청 스키마 | 응답 스키마 |
|----|-----------|------------|------------|
| accounts | POST /api/auth/login/ | LoginSerializer (기존) | LoginResponseSerializer |
| accounts | POST /api/auth/register/ | RegisterSerializer (기존) | RegisterResponseSerializer |
| accounts | GET /api/users/me/ | — | MeResponseSerializer |
| study | POST /api/analysis/validate/ | SessionCreateRequestSerializer | ValidateResponseSerializer |
| study | GET /api/sessions/ | query params | SessionSummarySerializer(many) |
| study | POST /api/sessions/ | SessionCreateRequestSerializer | SessionCreateResponseSerializer |
| study | GET /api/sessions/{id}/ | — | SessionDetailResponseSerializer |
| study | DELETE /api/sessions/{id}/ | — | OkResponseSerializer |
| study | GET /api/wrong-answers/ | — | WrongAnswerSerializer(many) |
| study | PATCH /api/wrong-answers/{id}/ | WrongAnswerUpdateRequestSerializer | WrongAnswerUpdateResponseSerializer |
| concepts | GET /api/concepts/ | — | ConceptSummarySerializer(many) |
| concepts | GET /api/concepts/{id}/ | — | ConceptDetailSerializer |
| analytics | GET /api/weak-concepts/ | — | WeakConceptSerializer(many) |
| analytics | GET /api/recommendations/review/ | — | RecommendationSerializer(many) |
| analytics | GET /api/dashboard/summary/ | — | DashboardResponseSerializer |
| analytics | GET /api/calendar/ | year, month | CalendarResponseSerializer |
| analytics | GET /api/study-comparison/ | session_id (필수) | StudyComparisonResponseSerializer |
| analytics | POST /api/problem-analysis/ | ProblemAnalysisRequestSerializer | ProblemAnalysisCreateResponseSerializer |
| analytics | GET /api/problem-analysis/ | — | ProblemAnalysisItemSerializer(many) |
| analytics | GET /api/reports/growth/ | period | GrowthReportResponseSerializer |

총 20개 엔드포인트 (TokenRefresh 제외)

---

## 브랜치 전략

- 베이스: `chore/consolidate-api-docs-and-swagger`
- 신규: `feat/swagger-schema`
- 완료 후 `feat/swagger-schema` PR 생성 (머지 없음)
