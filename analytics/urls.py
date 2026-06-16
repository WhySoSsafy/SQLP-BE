from django.urls import path
from analytics.views import WeakConceptsView, ReviewRecommendationsView, DashboardSummaryView, CalendarView

urlpatterns = [
    path("weak-concepts/", WeakConceptsView.as_view()),
    path("recommendations/review/", ReviewRecommendationsView.as_view()),
    path("dashboard/summary/", DashboardSummaryView.as_view()),
    path("calendar/", CalendarView.as_view()),
]
