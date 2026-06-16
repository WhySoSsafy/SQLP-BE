from study.services.scoring import participant_score, average_understanding


def session_detail(session):
    problems = []
    for problem in session.problems.all():
        problems.append({
            "id": problem.id,
            "problem_number": problem.problem_number,
            "subject_area": problem.subject_area,
            "concepts": [c.name for c in problem.concepts.all()],
            "solution_summary": problem.solution_summary,
            "participants": [{
                "name": pp.name,
                "is_correct": pp.is_correct,
                "understanding": pp.understanding,
                "concepts_covered": pp.concepts_covered,
                "concepts_missed": pp.concepts_missed,
                "errors": pp.errors,
                "review_required": pp.review_required,
            } for pp in problem.participants.all()],
        })
    speakers = sorted({pp["name"] for prob in problems for pp in prob["participants"]})
    return {
        "id": session.id,
        "session_date": str(session.session_date),
        "book": session.book,
        "speakers": speakers,
        "created_at": session.created_at.isoformat().replace("+00:00", "Z"),
        "problems": problems,
    }


def session_summary(session):
    scores = []
    speakers = set()
    review_required = 0
    problem_count = 0
    for problem in session.problems.all():
        problem_count += 1
        for pp in problem.participants.all():
            scores.append(participant_score(pp.understanding, pp.is_correct))
            speakers.add(pp.name)
            if pp.review_required:
                review_required += 1
    return {
        "id": session.id,
        "session_date": str(session.session_date),
        "book": session.book,
        "speakers": sorted(speakers),
        "problem_count": problem_count,
        "average_understanding": average_understanding(scores),
        "review_required_count": review_required,
        "created_at": session.created_at.isoformat().replace("+00:00", "Z"),
    }
