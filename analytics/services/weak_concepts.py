from collections import defaultdict

from django.conf import settings

from concepts.models import Concept
from study.models import ProblemParticipant
from study.services.scoring import participant_score, average_understanding


def weak_concepts(group):
    result = []
    for concept in Concept.objects.filter(group=group):
        pps = list(ProblemParticipant.objects.filter(
            # concept is already group-scoped (unique per group); session__group is defensive.
            problem__concepts=concept, problem__session__group=group
        ).select_related("problem", "problem__session"))
        if not pps:
            continue
        scores_by_person = defaultdict(list)
        weak_by_person = defaultdict(int)
        last_date = None
        problem_ids = set()
        for pp in pps:
            problem_ids.add(pp.problem_id)
            score = participant_score(pp.understanding, pp.is_correct)
            scores_by_person[pp.name].append(score)
            if pp.review_required or not pp.is_correct:
                weak_by_person[pp.name] += 1
            d = pp.problem.session.session_date
            if last_date is None or d > last_date:
                last_date = d
        score_by_person = {n: average_understanding(s) for n, s in scores_by_person.items()}
        all_scores = [s for ss in scores_by_person.values() for s in ss]
        avg = average_understanding(all_scores)
        result.append({
            "name": concept.name,
            "subject": concept.subject,
            "totalProblems": len(problem_ids),
            "weakCountByParticipant": dict(weak_by_person),
            "scoreByParticipant": score_by_person,
            "averageScore": avg,
            "lastReviewDate": str(last_date) if last_date else None,
            "recommend": avg < settings.WEAK_THRESHOLD,
        })
    result.sort(key=lambda x: x["averageScore"])
    return result
