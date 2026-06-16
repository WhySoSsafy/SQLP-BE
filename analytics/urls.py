from django.urls import path
from analytics.views import WeakConceptsView, ReviewRecommendationsView

urlpatterns = [
    path("weak-concepts/", WeakConceptsView.as_view()),
    path("recommendations/review/", ReviewRecommendationsView.as_view()),
]
