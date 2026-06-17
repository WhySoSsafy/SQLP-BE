import hashlib
from collections import Counter

from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.exceptions import APIException

from accounts.models import User
from concepts.models import Concept
from study.models import StudySession, Problem, ProblemParticipant
from study.services.slug import build_session_id


class DuplicateSession(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = ("같은 날짜, 문제집명, 문제번호 구성을 가진 학습 세션이 "
                      "이미 저장되어 있습니다.")
    default_code = "DUPLICATE_SESSION"


def _dedup_key(group, session_date, book, numbers):
    raw = f"{group.id}|{session_date}|{book}|{'-'.join(str(n) for n in numbers)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_MAX_SLUG_ATTEMPTS = 5


@transaction.atomic
def create_session(group, data):
    numbers = sorted({p["problem_number"] for p in data["problems"]})
    key = _dedup_key(group, data["session_date"], data["book"], numbers)
    if StudySession.objects.filter(dedup_key=key).exists():
        raise DuplicateSession()

    participant_names = {pp["name"] for p in data["problems"] for pp in p["participants"]}
    speakers = sorted(set(data["speakers"]) | participant_names)

    session = None
    for _ in range(_MAX_SLUG_ATTEMPTS):
        session_id = build_session_id(data["session_date"], data["book"], numbers)
        try:
            with transaction.atomic():  # savepoint: only this INSERT rolls back on clash
                session = StudySession.objects.create(
                    id=session_id, group=group,
                    session_date=data["session_date"], book=data["book"],
                    dedup_key=key, speakers=speakers,
                )
            break
        except IntegrityError:
            # dedup_key clash => a concurrent request created the same logical session.
            if StudySession.objects.filter(dedup_key=key).exists():
                raise DuplicateSession()
            # else PK-only clash: a concurrent session took this slug; rebuild and retry.
            continue
    if session is None:
        raise DuplicateSession()

    group_users = list(User.objects.filter(group=group))
    name_counts = Counter(u.name for u in group_users)
    # Only link names that unambiguously identify one member; duplicate display
    # names in a group are left unlinked rather than mislinked to the wrong user.
    members = {u.name: u for u in group_users if name_counts[u.name] == 1}
    for p in data["problems"]:
        problem = Problem.objects.create(
            id=f"{session_id}-p{p['problem_number']}", session=session,
            problem_number=p["problem_number"], subject_area=p["subject_area"],
            solution_summary=p["solution_summary"],
        )
        # First session to introduce a concept sets its subject; later sessions reuse it.
        for cname in p["concepts"]:
            concept, _ = Concept.objects.get_or_create(
                group=group, name=cname, defaults={"subject": p["subject_area"]},
            )
            problem.concepts.add(concept)
        for pp in p["participants"]:
            ProblemParticipant.objects.create(
                problem=problem, name=pp["name"], member=members.get(pp["name"]),
                is_correct=pp["is_correct"], understanding=pp["understanding"],
                concepts_covered=pp["concepts_covered"], concepts_missed=pp["concepts_missed"],
                errors=pp["errors"], review_required=pp["review_required"],
            )
    return session
