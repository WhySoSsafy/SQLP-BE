from django.conf import settings

from study.models import ProblemParticipant
from study.services.scoring import participant_score, average_understanding


def _participants_for_concept(concept):
    # Concept is unique per (group, name), so a Problem in another group can never
    # be M2M-linked to this concept instance — this filter is implicitly group-safe.
    return ProblemParticipant.objects.filter(problem__concepts=concept)


def concept_understanding(concept):
    scores = [participant_score(pp.understanding, pp.is_correct)
              for pp in _participants_for_concept(concept)]
    return average_understanding(scores)


def concept_review_recommended(concept, score=None):
    if score is None:
        score = concept_understanding(concept)
    return score < settings.WEAK_THRESHOLD
