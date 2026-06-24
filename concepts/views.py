from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from concepts.models import Concept
from concepts.services import concept_understanding, concept_review_recommended
from study.models import ProblemParticipant
from drf_spectacular.utils import extend_schema
from concepts.schema_serializers import ConceptSummarySerializer, ConceptDetailSerializer


@extend_schema(responses={200: ConceptSummarySerializer(many=True)})
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
