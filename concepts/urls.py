from django.urls import path
from concepts.views import ConceptListView, ConceptDetailView

urlpatterns = [
    path("concepts/", ConceptListView.as_view()),
    path("concepts/<int:concept_id>/", ConceptDetailView.as_view()),
]
