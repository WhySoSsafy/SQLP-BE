from collections import defaultdict

from django.shortcuts import get_object_or_404

from study.models import StudySession
from study.services.scoring import participant_score, average_understanding


def study_comparison(group, session_id):
    session = get_object_or_404(
        StudySession.objects.filter(group=group)
        .prefetch_related("problems__participants", "problems__concepts"),
        id=session_id,
    )
    per = defaultdict(lambda: {"scores": [], "correct": 0, "review": 0, "weak": set()})
    problems_out = []
    for problem in session.problems.all():
        concept_names = [c.name for c in problem.concepts.all()]  # served from prefetch cache
        p_participants = []
        for pp in problem.participants.all():
            agg = per[pp.name]
            agg["scores"].append(participant_score(pp.understanding, pp.is_correct))
            if pp.is_correct:
                agg["correct"] += 1
            if pp.review_required:
                agg["review"] += 1
            for missed in pp.concepts_missed:
                agg["weak"].add(missed)
            if pp.review_required or not pp.is_correct:
                agg["weak"].update(concept_names)
            p_participants.append({
                "name": pp.name,
                "isCorrect": pp.is_correct,
                "understanding": pp.understanding,
                "reviewRequired": pp.review_required,
            })
        problems_out.append({
            "problemNumber": problem.problem_number,
            "concepts": concept_names,
            "participants": p_participants,
        })
    participants = [{
        "name": name,
        "averageUnderstanding": average_understanding(v["scores"]),
        "correctCount": v["correct"],
        "reviewRequiredCount": v["review"],
        "weakConcepts": sorted(v["weak"]),
    } for name, v in sorted(per.items())]
    return {
        "sessionId": session.id,
        "book": session.book,
        "sessionDate": str(session.session_date),
        "participants": participants,
        "problems": problems_out,
    }
