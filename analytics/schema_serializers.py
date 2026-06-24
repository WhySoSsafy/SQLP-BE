from rest_framework import serializers


# ── WeakConcepts ─────────────────────────────────────────────────────────────

class WeakConceptSerializer(serializers.Serializer):
    name = serializers.CharField()
    subject = serializers.CharField()
    totalProblems = serializers.IntegerField()
    weakCountByParticipant = serializers.DictField(child=serializers.IntegerField())
    scoreByParticipant = serializers.DictField(child=serializers.FloatField())
    averageScore = serializers.FloatField()
    lastReviewDate = serializers.DateField(allow_null=True)
    recommend = serializers.BooleanField()


# ── Recommendations ───────────────────────────────────────────────────────────

class RecommendationSerializer(serializers.Serializer):
    concept = serializers.CharField()
    subject = serializers.CharField()
    reason = serializers.CharField()
    score = serializers.FloatField()


# ── Dashboard ─────────────────────────────────────────────────────────────────

class RecentSessionSerializer(serializers.Serializer):
    id = serializers.CharField()
    date = serializers.DateField()
    book = serializers.CharField()
    problemCount = serializers.IntegerField()
    averageUnderstanding = serializers.FloatField()


class DashboardResponseSerializer(serializers.Serializer):
    weeklyProblemCount = serializers.IntegerField()
    reviewRequiredCount = serializers.IntegerField()
    averageUnderstanding = serializers.FloatField()
    studyStreak = serializers.IntegerField()
    recommendations = RecommendationSerializer(many=True)
    recentSessions = RecentSessionSerializer(many=True)


# ── Calendar ──────────────────────────────────────────────────────────────────

class CalendarDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    problemCount = serializers.IntegerField()
    averageUnderstanding = serializers.FloatField()
    mainConcepts = serializers.ListField(child=serializers.CharField())
    reviewRequiredCount = serializers.IntegerField()


class CalendarResponseSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    days = CalendarDaySerializer(many=True)
    weeklyProblemCount = serializers.IntegerField()
    monthlyProblemCount = serializers.IntegerField()
    studyStreak = serializers.IntegerField()


# ── StudyComparison ───────────────────────────────────────────────────────────

class ComparisonParticipantSerializer(serializers.Serializer):
    name = serializers.CharField()
    averageUnderstanding = serializers.FloatField()
    correctCount = serializers.IntegerField()
    reviewRequiredCount = serializers.IntegerField()
    weakConcepts = serializers.ListField(child=serializers.CharField())


class ComparisonProblemParticipantSerializer(serializers.Serializer):
    name = serializers.CharField()
    isCorrect = serializers.BooleanField()
    understanding = serializers.CharField()
    reviewRequired = serializers.BooleanField()


class ComparisonProblemSerializer(serializers.Serializer):
    problemNumber = serializers.IntegerField()
    concepts = serializers.ListField(child=serializers.CharField())
    participants = ComparisonProblemParticipantSerializer(many=True)


class StudyComparisonResponseSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    book = serializers.CharField()
    sessionDate = serializers.DateField()
    participants = ComparisonParticipantSerializer(many=True)
    problems = ComparisonProblemSerializer(many=True)


# ── GrowthReport ──────────────────────────────────────────────────────────────

class TrendItemSerializer(serializers.Serializer):
    date = serializers.DateField()
    averageUnderstanding = serializers.FloatField()


class GrowthReportResponseSerializer(serializers.Serializer):
    period = serializers.CharField()
    problemCount = serializers.IntegerField()
    averageUnderstanding = serializers.FloatField()
    reviewRequiredCount = serializers.IntegerField()
    improvedConcepts = serializers.ListField(child=serializers.CharField())
    stillWeakConcepts = serializers.ListField(child=serializers.CharField())
    trend = TrendItemSerializer(many=True)


# ── ProblemAnalysis ───────────────────────────────────────────────────────────

class ProblemAnalysisInputSchemaSerializer(serializers.Serializer):
    problem_number = serializers.IntegerField()
    subject_area = serializers.CharField()
    concepts = serializers.ListField(child=serializers.CharField())
    estimated_difficulty = serializers.CharField()
    frequency = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.IntegerField(required=False)


class ProblemAnalysisRequestSerializer(serializers.Serializer):
    book = serializers.CharField()
    problems = ProblemAnalysisInputSchemaSerializer(many=True)


class ProblemAnalysisCreateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    created_count = serializers.IntegerField()
