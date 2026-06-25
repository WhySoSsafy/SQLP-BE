from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from concepts.models import Concept
from concepts.services import concept_understanding, concept_review_recommended
from study.models import ProblemParticipant
from drf_spectacular.utils import extend_schema
from rest_framework import status

from concepts.schema_serializers import (
    ConceptSummarySerializer,
    ConceptDetailSerializer,
    ConceptCreateSerializer,
    ConceptCreateResponseSerializer,
)


@extend_schema(
    methods=["GET"],
    responses={200: ConceptSummarySerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    request=ConceptCreateSerializer,
    responses={201: ConceptCreateResponseSerializer},
)
class ConceptListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        out = []
        for c in Concept.objects.filter(group=request.user.group):
            score = concept_understanding(c)
            out.append({
                "id": c.id,
                "name": c.name,
                "subject": c.subject,
                "summary": c.summary,
                "myUnderstanding": score,
                "reviewRecommended": concept_review_recommended(c, score),
            })
        return Response(out)

    def post(self, request):
        data = request.data

        # Resolve name: accept 'name' or 'title' alias.
        name_val = data.get("name") or data.get("title") or ""
        # Reject non-string JSON values (number/list/dict) with 400 instead of crashing (500).
        if not isinstance(name_val, str):
            return Response(
                {"detail": "name must be a string."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        name = name_val.strip()
        if not name:
            return Response(
                {"detail": "name is required and must not be blank."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Accept camelCase or snake_case for array fields
        frequent_question_types = (
            data.get("frequentQuestionTypes")
            or data.get("frequent_question_types")
            or []
        )
        confusing_points = (
            data.get("confusingPoints")
            or data.get("confusing_points")
            or []
        )
        wrong_patterns = (
            data.get("wrongPatterns")
            or data.get("wrong_patterns")
            or []
        )

        # `or ""` normalizes explicit JSON null → "" (CharField/TextField are non-null).
        subject = data.get("subject") or ""
        summary = data.get("summary") or ""

        concept, _ = Concept.objects.update_or_create(
            group=request.user.group,
            name=name,
            defaults={
                "subject": subject,
                "summary": summary,
                "frequent_question_types": frequent_question_types,
                "confusing_points": confusing_points,
                "wrong_patterns": wrong_patterns,
            },
        )

        return Response(
            {
                "id": concept.id,
                "name": concept.name,
                "subject": concept.subject,
                "summary": concept.summary,
                "frequentQuestionTypes": concept.frequent_question_types,
                "confusingPoints": concept.confusing_points,
                "wrongPatterns": concept.wrong_patterns,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(responses={200: ConceptDetailSerializer})
class ConceptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, concept_id):
        concept = get_object_or_404(Concept, group=request.user.group, id=concept_id)
        related = []
        participants = (ProblemParticipant.objects
                        # concept is already group-scoped via get_object_or_404; the
                        # session__group filter is defensive and harmless.
                        .filter(problem__concepts=concept,
                                problem__session__group=request.user.group)
                        .select_related("problem", "problem__session"))
        for pp in participants:
            related.append({
                "sessionId": pp.problem.session_id,
                "problemNumber": pp.problem.problem_number,
                "person": pp.name,
                "understanding": pp.understanding,
                "reviewRequired": pp.review_required,
            })
        score = concept_understanding(concept)
        return Response({
            "id": concept.id,
            "name": concept.name,
            "subject": concept.subject,
            "summary": concept.summary,
            "frequentQuestionTypes": concept.frequent_question_types,
            "confusingPoints": concept.confusing_points,
            "wrongPatterns": concept.wrong_patterns,
            "relatedProblems": related,
            "myUnderstanding": score,
            "reviewRecommended": concept_review_recommended(concept, score),
        })
