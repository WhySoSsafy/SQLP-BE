from rest_framework import serializers
from analytics.models import ProblemAnalysis


class ProblemAnalysisItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemAnalysis
        fields = ["id", "book", "problem_number", "subject_area", "concepts",
                  "estimated_difficulty", "frequency", "priority"]


class ProblemAnalysisInputSerializer(serializers.Serializer):
    problem_number = serializers.IntegerField(min_value=1, max_value=2147483647)
    subject_area = serializers.CharField(max_length=100)
    concepts = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)
    estimated_difficulty = serializers.CharField(max_length=10)
    frequency = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    priority = serializers.IntegerField(required=False, default=0, min_value=-2147483648, max_value=2147483647)


class ProblemAnalysisBulkSerializer(serializers.Serializer):
    book = serializers.CharField(max_length=200)
    problems = ProblemAnalysisInputSerializer(many=True, allow_empty=False)
