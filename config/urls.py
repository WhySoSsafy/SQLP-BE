from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("accounts.urls")),
    path("api/", include("study.urls")),
    path("api/", include("concepts.urls")),
    path("api/", include("analytics.urls")),
]
