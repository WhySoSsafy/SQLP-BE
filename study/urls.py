from django.urls import path
from study.views import ValidateView, SessionListCreateView, SessionDetailView

urlpatterns = [
    path("analysis/validate/", ValidateView.as_view()),
    path("sessions/", SessionListCreateView.as_view()),
    path("sessions/<str:session_id>/", SessionDetailView.as_view()),
]
