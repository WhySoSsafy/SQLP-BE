from django.urls import path
from study.views import ValidateView, SessionListCreateView, SessionDetailView, WrongAnswerListView, WrongAnswerDetailView

urlpatterns = [
    path("analysis/validate/", ValidateView.as_view()),
    path("sessions/", SessionListCreateView.as_view()),
    path("sessions/<str:session_id>/", SessionDetailView.as_view()),
    path("wrong-answers/", WrongAnswerListView.as_view()),
    path("wrong-answers/<path:wrong_answer_id>/", WrongAnswerDetailView.as_view()),
]
