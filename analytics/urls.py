from django.urls import path
from analytics.views import WeakConceptsView

urlpatterns = [
    path("weak-concepts/", WeakConceptsView.as_view()),
]
