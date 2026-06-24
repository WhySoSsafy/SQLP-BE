from rest_framework import serializers


# ── 요청 스키마 ──────────────────────────────────────────────────────────────

class ParticipantInputSerializer(serializers.Serializer):
    name = serializers.CharField()
    is_correct = serializers.BooleanField()
    understanding = serializers.ChoiceField(choices=["이해", "애매", "모름"])
    concepts_covered = serializers.ListField(child=serializers.CharField())
    concepts_missed = serializers.ListField(child=serializers.CharField())
    errors = serializers.ListField(child=serializers.CharField())
    review_required = serializers.BooleanField()


class ProblemInputSerializer(serializers.Serializer):
    problem_number = serializers.IntegerField()
    subject_area = serializers.CharField()
    solution_summary = serializers.CharField()
    concepts = serializers.ListField(child=serializers.CharField())
    participants = ParticipantInputSerializer(many=True)


class SessionCreateRequestSerializer(serializers.Serializer):
    session_date = serializers.DateField()
    book = serializers.CharField()
    speakers = serializers.ListField(child=serializers.CharField())
    problems = ProblemInputSerializer(many=True)


class WrongAnswerUpdateRequestSerializer(serializers.Serializer):
    done = serializers.BooleanField()


# ── 응답 스키마 ──────────────────────────────────────────────────────────────

class OkResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()


class SessionCreateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    session_id = serializers.CharField()


class SessionSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    book = serializers.CharField()
    session_date = serializers.DateField()
    problem_count = serializers.IntegerField()
    average_understanding = serializers.FloatField()
    speakers = serializers.ListField(child=serializers.CharField())


class ParticipantDetailSerializer(serializers.Serializer):
    name = serializers.CharField()
    is_correct = serializers.BooleanField()
    understanding = serializers.CharField()
    concepts_covered = serializers.ListField(child=serializers.CharField())
    concepts_missed = serializers.ListField(child=serializers.CharField())
    errors = serializers.ListField(child=serializers.CharField())
    review_required = serializers.BooleanField()


class ProblemDetailSerializer(serializers.Serializer):
    id = serializers.CharField()
    problem_number = serializers.IntegerField()
    subject_area = serializers.CharField()
    solution_summary = serializers.CharField()
    concepts = serializers.ListField(child=serializers.CharField())
    participants = ParticipantDetailSerializer(many=True)


class SessionDetailResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    book = serializers.CharField()
    session_date = serializers.DateField()
    speakers = serializers.ListField(child=serializers.CharField())
    problems = ProblemDetailSerializer(many=True)


class ValidatePreviewSerializer(serializers.Serializer):
    sessionDate = serializers.DateField()
    book = serializers.CharField()
    problemCount = serializers.IntegerField()
    participantCount = serializers.IntegerField()
    conceptTags = serializers.ListField(child=serializers.CharField())


class ValidateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    preview = ValidatePreviewSerializer()


class WrongAnswerSerializer(serializers.Serializer):
    id = serializers.CharField()
    problem_number = serializers.IntegerField()
    book = serializers.CharField()
    session_date = serializers.DateField()
    understanding = serializers.CharField()
    review_required = serializers.BooleanField()
    done = serializers.BooleanField()


class WrongAnswerUpdateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    id = serializers.CharField()
    done = serializers.BooleanField()
