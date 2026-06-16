from django.urls import path
from study.views import ValidateView

urlpatterns = [
    path("analysis/validate/", ValidateView.as_view()),
]
