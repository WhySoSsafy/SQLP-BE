from rest_framework import serializers


class ConceptCreateSerializer(serializers.Serializer):
    """Request body for POST /api/concepts/. Accepts camelCase or snake_case."""
    name = serializers.CharField(required=False, allow_blank=True, default="")
    title = serializers.CharField(required=False, allow_blank=True, default="")
    subject = serializers.CharField(required=False, allow_blank=True, default="")
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    frequentQuestionTypes = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    confusingPoints = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    wrongPatterns = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class ConceptCreateResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subject = serializers.CharField()
    summary = serializers.CharField()
    frequentQuestionTypes = serializers.ListField(child=serializers.CharField())
    confusingPoints = serializers.ListField(child=serializers.CharField())
    wrongPatterns = serializers.ListField(child=serializers.CharField())


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
