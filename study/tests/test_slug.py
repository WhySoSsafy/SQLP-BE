import pytest
from accounts.models import StudyGroup
from study.models import StudySession
from study.services.slug import build_session_id

pytestmark = pytest.mark.django_db

def test_slug_format():
    sid = build_session_id("2026-06-13", "SQLP 실전문제", [1, 2])
    assert sid == "2026-06-13-sqlp-실전문제-1-2"

def test_slug_collision_suffix():
    g = StudyGroup.get_default()
    StudySession.objects.create(id="2026-06-13-sqlp-실전문제-1", group=g,
                                session_date="2026-06-13", book="SQLP 실전문제")
    sid = build_session_id("2026-06-13", "SQLP 실전문제", [1])
    assert sid == "2026-06-13-sqlp-실전문제-1-2"

def test_slug_collision_across_groups():
    g1 = StudyGroup.get_default()
    g2 = StudyGroup.objects.create(name="other", slug="other")
    StudySession.objects.create(id="2026-06-13-sqlp-실전문제-1", group=g2,
                                session_date="2026-06-13", book="SQLP 실전문제")
    # id is the global PK, so a slug taken by another group must still be avoided
    sid = build_session_id("2026-06-13", "SQLP 실전문제", [1])
    assert sid == "2026-06-13-sqlp-실전문제-1-2"

def test_slug_sorts_problem_numbers():
    sid = build_session_id("2026-06-13", "SQLP 실전문제", [2, 1])
    assert sid == "2026-06-13-sqlp-실전문제-1-2"

def test_slug_dedupes_problem_numbers():
    sid = build_session_id("2026-06-13", "SQLP 실전문제", [1, 1, 2])
    assert sid == "2026-06-13-sqlp-실전문제-1-2"

def test_slug_chained_collision():
    g = StudyGroup.get_default()
    StudySession.objects.create(id="2026-06-13-sqlp-실전문제-1", group=g,
                                session_date="2026-06-13", book="SQLP 실전문제")
    StudySession.objects.create(id="2026-06-13-sqlp-실전문제-1-2", group=g,
                                session_date="2026-06-13", book="SQLP 실전문제")
    sid = build_session_id("2026-06-13", "SQLP 실전문제", [1])
    assert sid == "2026-06-13-sqlp-실전문제-1-3"

def test_slug_accepts_date_object():
    from datetime import date
    sid = build_session_id(date(2026, 6, 13), "SQLP 실전문제", [1])
    assert sid == "2026-06-13-sqlp-실전문제-1"

def test_slug_raises_on_empty_problem_numbers():
    with pytest.raises(ValueError):
        build_session_id("2026-06-13", "SQLP 실전문제", [])

def test_slug_respects_max_length():
    long_book = "가" * 300
    sid = build_session_id("2026-06-13", long_book, [1, 2, 3])
    assert len(sid) <= 255

def test_slug_respects_max_length_with_many_numbers():
    sid = build_session_id("2026-06-13", "SQLP 실전문제", list(range(1, 200)))
    assert len(sid) <= 255
