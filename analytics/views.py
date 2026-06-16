from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.services.weak_concepts import weak_concepts
from analytics.services.recommendations import review_recommendations
from analytics.services.dashboard import dashboard_summary
from analytics.services.calendar import calendar_data


class WeakConceptsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(weak_concepts(request.user.group))


class ReviewRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(review_recommendations(request.user.group))


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(dashboard_summary(request.user.group))


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
