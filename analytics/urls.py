from django.urls import path
from analytics.views import WeakConceptsView, ReviewRecommendationsView, DashboardSummaryView, CalendarView, StudyComparisonView, ProblemAnalysisView, GrowthReportView

urlpatterns = [
    path("weak-concepts/", WeakConceptsView.as_view()),
    path("recommendations/review/", ReviewRecommendationsView.as_view()),
    path("dashboard/summary/", DashboardSummaryView.as_view()),
    path("calendar/", CalendarView.as_view()),
    path("study-comparison/", StudyComparisonView.as_view()),
    path("problem-analysis/", ProblemAnalysisView.as_view()),
    path("reports/growth/", GrowthReportView.as_view()),
]
