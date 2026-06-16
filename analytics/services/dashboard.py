from datetime import timedelta

from django.utils import timezone

from study.models import Problem, ProblemParticipant, StudySession
from study.services.scoring import participant_score, average_understanding
from study.services.serialize import session_summary
from analytics.services.recommendations import review_recommendations


def _study_streak(group):
    dates = set(StudySession.objects.filter(group=group)
                .values_list("session_date", flat=True))
    if not dates:
        return 0
    today = timezone.now().date()
    cursor = today if today in dates else today - timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def dashboard_summary(group):
    week_ago = timezone.now().date() - timedelta(days=7)
    weekly_problems = Problem.objects.filter(
        session__group=group, session__session_date__gte=week_ago).count()
    review_required = ProblemParticipant.objects.filter(
        problem__session__group=group, review_required=True).count()
    all_scores = [participant_score(pp.understanding, pp.is_correct)
                  for pp in ProblemParticipant.objects.filter(problem__session__group=group)]
    recent = (StudySession.objects.filter(group=group)
              .order_by("-session_date", "-created_at")
              .prefetch_related("problems__participants")[:5])
    recent_out = []
    for s in recent:
        summ = session_summary(s)
        recent_out.append({
            "id": summ["id"], "date": summ["session_date"], "book": summ["book"],
            "problemCount": summ["problem_count"],
            "averageUnderstanding": summ["average_understanding"],
        })
    return {
        "weeklyProblemCount": weekly_problems,
        "reviewRequiredCount": review_required,
        "averageUnderstanding": average_understanding(all_scores),
        "studyStreak": _study_streak(group),
        "recommendations": review_recommendations(group, limit=5),
        "recentSessions": recent_out,
    }
