from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.services.weak_concepts import weak_concepts
from analytics.services.recommendations import review_recommendations
from analytics.services.dashboard import dashboard_summary


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
