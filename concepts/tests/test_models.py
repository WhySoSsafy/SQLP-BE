import pytest
from django.db import IntegrityError, transaction
from accounts.models import StudyGroup
from concepts.models import Concept

pytestmark = pytest.mark.django_db

def test_concept_unique_per_group():
    g = StudyGroup.get_default()
    Concept.objects.create(group=g, name="OUTER JOIN", subject="SQL 기본 및 활용")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Concept.objects.create(group=g, name="OUTER JOIN", subject="SQL 기본 및 활용")
