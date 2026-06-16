from datetime import date

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from study.models import StudySession
from study.serializers import SessionInputSerializer
from study.services.serialize import session_summary
from study.services.session_create import create_session


def _parse_date_param(value, field):
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({field: ["유효한 날짜(YYYY-MM-DD)가 아닙니다."]})


class SessionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (StudySession.objects.filter(group=request.user.group)
              .prefetch_related("problems__participants"))
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(book__icontains=search)
        date_from = request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(session_date__gte=_parse_date_param(date_from, "date_from"))
        date_to = request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(session_date__lte=_parse_date_param(date_to, "date_to"))
        rows = [session_summary(s) for s in qs]
        understanding = request.query_params.get("understanding")
        if understanding == "high":
            rows = [r for r in rows if r["average_understanding"] >= 70]
        elif understanding == "low":
            rows = [r for r in rows if r["average_understanding"] < 50]
        return Response(rows)

    def post(self, request):
        serializer = SessionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = create_session(request.user.group, serializer.validated_data)
        return Response({"ok": True, "session_id": session.id},
                        status=status.HTTP_201_CREATED)


class ValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SessionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        concept_tags = []
        for p in data["problems"]:
            for c in p["concepts"]:
                if c not in concept_tags:
                    concept_tags.append(c)
        participants = {pp["name"] for p in data["problems"] for pp in p["participants"]}
        preview = {
            "sessionDate": str(data["session_date"]),
            "book": data["book"],
            "problemCount": len(data["problems"]),
            "participantCount": len(participants | set(data["speakers"])),
            "conceptTags": concept_tags,
        }
        return Response({"ok": True, "preview": preview})
