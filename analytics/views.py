from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from analytics.models import ProblemAnalysis
from analytics.serializers import ProblemAnalysisBulkSerializer, ProblemAnalysisItemSerializer
from analytics.services.weak_concepts import weak_concepts
from analytics.services.recommendations import review_recommendations
from analytics.services.dashboard import dashboard_summary
from analytics.services.calendar import calendar_data
from analytics.services.comparison import study_comparison
from analytics.services.reports import growth_report
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


@extend_schema(responses={200: WeakConceptSerializer(many=True)})
class WeakConceptsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(weak_concepts(request.user.group))


@extend_schema(responses={200: RecommendationSerializer(many=True)})
class ReviewRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(review_recommendations(request.user.group))


@extend_schema(responses={200: DashboardResponseSerializer})
class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(dashboard_summary(request.user.group))


@extend_schema(
    parameters=[
        OpenApiParameter("year", int, required=True, description="조회 연도 (예: 2026)"),
        OpenApiParameter("month", int, required=True, description="조회 월 (1-12)"),
    ],
    responses={200: CalendarResponseSerializer},
)
class CalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        try:
            year = int(request.query_params.get("year", now.year))
            month = int(request.query_params.get("month", now.month))
        except (TypeError, ValueError):
            raise ValidationError({"year/month": ["정수여야 합니다."]})
        if not (1 <= month <= 12):
            raise ValidationError({"month": ["1~12 사이여야 합니다."]})
        if not (1 <= year <= 9999):
            raise ValidationError({"year": ["유효한 연도여야 합니다."]})
        return Response(calendar_data(request.user.group, year, month))


@extend_schema(
    parameters=[
        OpenApiParameter("session_id", str, required=True, description="비교할 세션 ID"),
    ],
    responses={200: StudyComparisonResponseSerializer},
)
class StudyComparisonView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            raise ValidationError({"session_id": ["필수 값입니다."]})
        return Response(study_comparison(request.user.group, session_id))


@extend_schema_view(
    get=extend_schema(responses={200: ProblemAnalysisItemSerializer(many=True)}),
    post=extend_schema(
        request=ProblemAnalysisRequestSerializer,
        responses={201: ProblemAnalysisCreateResponseSerializer},
    ),
)
class ProblemAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProblemAnalysisBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        objs = [ProblemAnalysis(group=request.user.group, book=data["book"], **p)
                for p in data["problems"]]
        ProblemAnalysis.objects.bulk_create(objs)
        return Response({"ok": True, "created_count": len(objs)},
                        status=status.HTTP_201_CREATED)

    def get(self, request):
        qs = ProblemAnalysis.objects.filter(group=request.user.group)
        return Response(ProblemAnalysisItemSerializer(qs, many=True).data)


@extend_schema(
    parameters=[
        OpenApiParameter("period", str, default="monthly", description="기간 (현재 echo-only, 항상 전체 기간 반환)"),
    ],
    responses={200: GrowthReportResponseSerializer},
)
class GrowthReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "monthly")
        return Response(growth_report(request.user.group, period))
