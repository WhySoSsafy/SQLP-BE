import pytest
from rest_framework.test import APIClient
from accounts.models import User
from concepts.models import Concept
from concepts.services import concept_understanding, concept_review_recommended
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _create_session():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u)
    c.post("/api/sessions/", PAYLOAD, format="json")
    return u

def test_concept_understanding_in_range():
    u = _create_session()
    concept = Concept.objects.get(group=u.group, name="OUTER JOIN")
    score = concept_understanding(concept)
    assert 0 <= score <= 100
    # 세은: 애매(50)*0.7 + correct(100)*0.3 = 65
    assert score == 65

def test_concept_review_recommended_threshold():
    u = _create_session()
    concept = Concept.objects.get(group=u.group, name="OUTER JOIN")
    # score 65 >= 50 (WEAK_THRESHOLD) => not recommended
    assert concept_review_recommended(concept) is False

def test_concept_with_no_participants_scores_zero():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    concept = Concept.objects.create(group=u.group, name="LONELY", subject="x")
    assert concept_understanding(concept) == 0
    # 0 < 50 => recommended
    assert concept_review_recommended(concept) is True
