from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from study.serializers import SessionInputSerializer
from study.services.session_create import create_session


class SessionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

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
