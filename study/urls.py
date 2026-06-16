from django.urls import path
from study.views import ValidateView, SessionListCreateView

urlpatterns = [
    path("analysis/validate/", ValidateView.as_view()),
    path("sessions/", SessionListCreateView.as_view()),
]
