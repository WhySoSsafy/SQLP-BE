from analytics.services.weak_concepts import weak_concepts

REVIEW_REASON = "모름/오답 반복으로 우선 복습이 필요해요."


def review_recommendations(group, limit=10):
    out = []
    for w in weak_concepts(group):
        if not w["recommend"]:
            continue
        out.append({
            "concept": w["name"],
            "subject": w["subject"],
            "reason": REVIEW_REASON,
            "score": w["averageScore"],
        })
    return out[:limit]
