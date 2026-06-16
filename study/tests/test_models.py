import pytest
from accounts.models import StudyGroup
from study.models import StudySession, Problem, ProblemParticipant

pytestmark = pytest.mark.django_db

def test_session_problem_participant_chain():
    g = StudyGroup.get_default()
    s = StudySession.objects.create(id="2026-06-13-x-1", group=g,
                                    session_date="2026-06-13", book="SQLP 실전문제")
    p = Problem.objects.create(id=f"{s.id}-p1", session=s, problem_number=1,
                               subject_area="SQL 기본 및 활용", solution_summary="요약")
    pp = ProblemParticipant.objects.create(problem=p, name="세은", is_correct=True,
                                           understanding="애매", review_required=True)
    assert pp.done is False
    assert s.problems.count() == 1
    assert p.participants.count() == 1

def test_wrong_answer_id_property():
    g = StudyGroup.get_default()
    s = StudySession.objects.create(id="2026-06-13-x-1", group=g,
                                    session_date="2026-06-13", book="SQLP 실전문제")
    p = Problem.objects.create(id=f"{s.id}-p1", session=s, problem_number=1,
                               subject_area="SQL 기본 및 활용")
    pp = ProblemParticipant.objects.create(problem=p, name="세은", understanding="모름")
    assert pp.wrong_answer_id == "2026-06-13-x-1-p1::세은"

def test_array_fields_default_to_empty_lists():
    g = StudyGroup.get_default()
    s = StudySession.objects.create(id="2026-06-13-x-1", group=g,
                                    session_date="2026-06-13", book="b")
    p = Problem.objects.create(id=f"{s.id}-p1", session=s, problem_number=1,
                               subject_area="x")
    pp = ProblemParticipant.objects.create(problem=p, name="세은", understanding="모름")
    assert pp.concepts_covered == []
    assert pp.concepts_missed == []
    assert pp.errors == []

def test_duplicate_participant_per_problem_rejected():
    from django.db import IntegrityError, transaction
    g = StudyGroup.get_default()
    s = StudySession.objects.create(id="2026-06-13-x-1", group=g,
                                    session_date="2026-06-13", book="b")
    p = Problem.objects.create(id=f"{s.id}-p1", session=s, problem_number=1,
                               subject_area="x")
    ProblemParticipant.objects.create(problem=p, name="세은", understanding="모름")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ProblemParticipant.objects.create(problem=p, name="세은", understanding="이해")
