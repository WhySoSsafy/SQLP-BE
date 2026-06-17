from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from study.models import StudySession
from study.services.scoring import participant_score, average_understanding


def calendar_data(group, year, month):
    sessions = (StudySession.objects.filter(
        group=group, session_date__year=year, session_date__month=month)
        .prefetch_related("problems__participants", "problems__concepts"))
    by_day = defaultdict(lambda: {"problems": 0, "scores": [],
                                  "concepts": defaultdict(int), "review": 0})
    for s in sessions:
        bucket = by_day[s.session_date.isoformat()]
        for problem in s.problems.all():
            bucket["problems"] += 1
            for c in problem.concepts.all():
                bucket["concepts"][c.name] += 1
            for pp in problem.participants.all():
                bucket["scores"].append(participant_score(pp.understanding, pp.is_correct))
                if pp.review_required:
                    bucket["review"] += 1
    days = []
    for date, b in sorted(by_day.items()):
        main = sorted(b["concepts"], key=lambda k: (-b["concepts"][k], k))[:3]
        days.append({
            "date": date,
            "problemCount": b["problems"],
            "averageUnderstanding": average_understanding(b["scores"]),
            "mainConcepts": main,
            "reviewRequiredCount": b["review"],
        })
    monthly = sum(d["problemCount"] for d in days)
    # weeklyProblemCount is relative to TODAY (not the queried month): it reflects
    # the current week [today-7, today], so it is 0 when viewing a past month and
    # excludes future-dated sessions.
    today = timezone.now().date()
    week_ago = (today - timedelta(days=7)).isoformat()
    today_str = today.isoformat()
    weekly = sum(d["problemCount"] for d in days if week_ago <= d["date"] <= today_str)
    return {
        "year": year, "month": month, "days": days,
        "weeklyProblemCount": weekly, "monthlyProblemCount": monthly,
        # studyStreak here = count of distinct active study days in the queried month;
        # the dashboard endpoint owns the authoritative consecutive-day streak.
        "studyStreak": len(by_day),
    }
