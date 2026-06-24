from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from study.models import StudySession
from study.serializers import SessionInputSerializer
from study.services.serialize import session_detail, session_summary
from study.services.session_create import create_session
from study.services.wrong_answers import wrong_answer_queryset, serialize_wrong_answer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from study.schema_serializers import (
    SessionCreateRequestSerializer,
    SessionSummarySerializer,
    SessionDetailResponseSerializer,
    SessionCreateResponseSerializer,
    ValidateResponseSerializer,
    WrongAnswerSerializer,
    WrongAnswerUpdateRequestSerializer,
    WrongAnswerUpdateResponseSerializer,
    OkResponseSerializer,
)


def _parse_date_param(value, field):
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({field: ["유효한 날짜(YYYY-MM-DD)가 아닙니다."]})


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter("search", str, description="책 제목 또는 참가자명 검색"),
            OpenApiParameter("understanding", str, enum=["high", "low"], description="이해도 필터 (high: 70점 이상, low: 50점 미만)"),
            OpenApiParameter("date_from", str, description="시작 날짜 (YYYY-MM-DD)"),
            OpenApiParameter("date_to", str, description="종료 날짜 (YYYY-MM-DD)"),
        ],
        responses={200: SessionSummarySerializer(many=True)},
    ),
    post=extend_schema(
        request=SessionCreateRequestSerializer,
        responses={201: SessionCreateResponseSerializer},
    ),
)
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


@extend_schema_view(
    get=extend_schema(responses={200: SessionDetailResponseSerializer}),
    delete=extend_schema(responses={200: OkResponseSerializer}),
)
class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_session(self, request, session_id):
        return get_object_or_404(
            StudySession.objects.filter(group=request.user.group)
            .prefetch_related("problems__participants", "problems__concepts"),
            id=session_id,
        )

    def get(self, request, session_id):
        return Response(session_detail(self._get_session(request, session_id)))

    def delete(self, request, session_id):
        self._get_session(request, session_id).delete()
        return Response({"ok": True})


@extend_schema(
    responses={200: WrongAnswerSerializer(many=True)},
)
class WrongAnswerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = wrong_answer_queryset(request.user.group)
        return Response([serialize_wrong_answer(pp) for pp in qs])


@extend_schema(
    request=WrongAnswerUpdateRequestSerializer,
    responses={200: WrongAnswerUpdateResponseSerializer},
)
class WrongAnswerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, wrong_answer_id):
        if not isinstance(request.data, dict):
            raise ValidationError({"detail": ["JSON 객체 본문이 필요합니다."]})
        done = request.data.get("done")
        if not isinstance(done, bool):
            raise ValidationError({"done": ["불리언 값이 필요합니다."]})
        # wrong_answer_id is "{problem_id}::{name}"; slugs use '-', never '::',
        # so splitting on the first '::' deterministically recovers both parts.
        parts = wrong_answer_id.split("::", 1)
        if len(parts) != 2:
            raise NotFound("오답노트를 찾을 수 없습니다.")
        problem_id, name = parts
        pp = get_object_or_404(
            wrong_answer_queryset(request.user.group),
            problem_id=problem_id, name=name,
        )
        pp.done = done
        pp.save(update_fields=["done"])
        return Response({"ok": True, "id": wrong_answer_id, "done": pp.done})


@extend_schema(
    request=SessionCreateRequestSerializer,
    responses={200: ValidateResponseSerializer},
)
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
