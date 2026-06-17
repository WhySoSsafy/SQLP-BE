from collections import defaultdict

from django.conf import settings

from study.models import Problem, ProblemParticipant
from study.services.scoring import participant_score, average_understanding
from analytics.services.weak_concepts import weak_concepts


def growth_report(group, period="monthly"):
    # `period` is currently an echo-only label (no date windowing is applied);
    # all of the group's history is summarized regardless of its value.
    problems = Problem.objects.filter(session__group=group)
    pps = list(ProblemParticipant.objects.filter(problem__session__group=group)
               .select_related("problem", "problem__session"))
    scored = [(pp, participant_score(pp.understanding, pp.is_correct)) for pp in pps]
    all_scores = [score for _, score in scored]
    review_required = sum(1 for pp in pps if pp.review_required)

    by_date = defaultdict(list)
    for pp, score in scored:
        by_date[pp.problem.session.session_date.isoformat()].append(score)
    trend = [{"date": d, "averageUnderstanding": average_understanding(s)}
             for d, s in sorted(by_date.items())]

    weak = weak_concepts(group)
    still_weak = [w["name"] for w in weak if w["averageScore"] < settings.WEAK_THRESHOLD]
    improved = [w["name"] for w in weak if w["averageScore"] >= settings.IMPROVED_THRESHOLD]
    return {
        "period": period,
        "problemCount": problems.count(),
        "averageUnderstanding": average_understanding(all_scores),
        "reviewRequiredCount": review_required,
        "improvedConcepts": improved,
        "stillWeakConcepts": still_weak,
        "trend": trend,
    }
