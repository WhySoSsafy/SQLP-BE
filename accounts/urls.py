from django.urls import path
from accounts.views import RegisterView, MeView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("users/me/", MeView.as_view()),
]
