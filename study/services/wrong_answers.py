from django.db.models import Q

from study.models import ProblemParticipant


def wrong_answer_queryset(group):
    return (ProblemParticipant.objects
            .filter(problem__session__group=group)
            .filter(Q(review_required=True) | Q(is_correct=False))
            .select_related("problem", "problem__session")
            .prefetch_related("problem__concepts"))


def serialize_wrong_answer(pp):
    problem = pp.problem
    session = problem.session
    return {
        "id": pp.wrong_answer_id,
        "sessionId": session.id,
        "problemId": problem.id,
        "problemNumber": problem.problem_number,
        "sessionDate": str(session.session_date),
        "book": session.book,
        "person": pp.name,
        "concepts": [c.name for c in problem.concepts.all()],
        "understanding": pp.understanding,
        "missed": pp.concepts_missed,
        "errors": pp.errors,
        "explanation": problem.solution_summary,
        "isCorrect": pp.is_correct,
        "reviewRequired": pp.review_required,
        "done": pp.done,
    }
