from django.conf import settings


def participant_score(understanding, is_correct):
    base = settings.UNDERSTANDING_SCORE.get(understanding, 0)
    correct = 100 if is_correct else 0
    score = base * settings.SCORE_UNDERSTANDING_WEIGHT + correct * settings.SCORE_CORRECT_WEIGHT
    return round(score)


def average_understanding(scores):
    if not scores:
        return 0
    return round(sum(scores) / len(scores))
