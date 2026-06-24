from rest_framework import serializers


class RelatedProblemSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    problemNumber = serializers.IntegerField()
    person = serializers.CharField()
    understanding = serializers.CharField()
    reviewRequired = serializers.BooleanField()


class ConceptSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subject = serializers.CharField()
    summary = serializers.CharField(allow_null=True)
    myUnderstanding = serializers.FloatField()
    reviewRecommended = serializers.BooleanField()


class ConceptDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subject = serializers.CharField()
    summary = serializers.CharField(allow_null=True)
    frequentQuestionTypes = serializers.ListField(child=serializers.CharField())
    confusingPoints = serializers.ListField(child=serializers.CharField())
    wrongPatterns = serializers.ListField(child=serializers.CharField())
    relatedProblems = RelatedProblemSerializer(many=True)
    myUnderstanding = serializers.FloatField()
    reviewRecommended = serializers.BooleanField()
