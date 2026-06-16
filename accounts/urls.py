from django.urls import path
from accounts.views import RegisterView, MeView
from accounts.jwt import LoginView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("users/me/", MeView.as_view()),
]
