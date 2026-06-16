from rest_framework import serializers
from study.models import UNDERSTANDING_CHOICES

UNDERSTANDING_VALUES = [c[0] for c in UNDERSTANDING_CHOICES]


class ParticipantInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    is_correct = serializers.BooleanField()
    understanding = serializers.ChoiceField(choices=UNDERSTANDING_VALUES)
    concepts_covered = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)
    concepts_missed = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)
    errors = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    review_required = serializers.BooleanField(default=False)


class ProblemInputSerializer(serializers.Serializer):
    problem_number = serializers.IntegerField(min_value=1)
    subject_area = serializers.CharField(max_length=100)
    concepts = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)
    solution_summary = serializers.CharField(required=False, allow_blank=True, default="")
    participants = ParticipantInputSerializer(many=True, allow_empty=False)

    def validate_participants(self, value):
        names = [p["name"] for p in value]
        if len(names) != len(set(names)):
            raise serializers.ValidationError("participant name must be unique within a problem.")
        return value


class SessionInputSerializer(serializers.Serializer):
    session_date = serializers.DateField()
    book = serializers.CharField(max_length=200)
    speakers = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    problems = ProblemInputSerializer(many=True, allow_empty=False)

    def validate_problems(self, value):
        numbers = [p["problem_number"] for p in value]
        if len(numbers) != len(set(numbers)):
            raise serializers.ValidationError("problem_number must be unique within a session.")
        return value
