from datetime import date

from django.utils.text import slugify

from study.models import StudySession

_SUFFIX_HEADROOM = 6  # room for a "-NNNNN" collision suffix within the PK max_length
_MAX_SUFFIX = 99999   # 5 digits, fits within _SUFFIX_HEADROOM ("-99999")


def build_session_id(session_date, book, problem_numbers, max_length=255) -> str:
    if not problem_numbers:
        raise ValueError("problem_numbers must not be empty")
    date_str = session_date.isoformat() if isinstance(session_date, date) else str(session_date)
    nums = "-".join(str(n) for n in sorted(set(problem_numbers)))
    book_slug = slugify(book, allow_unicode=True)
    budget = max_length - _SUFFIX_HEADROOM - len(date_str) - len(nums) - 2
    if budget > 0 and len(book_slug) > budget:
        book_slug = book_slug[:budget]
    base = f"{date_str}-{book_slug}-{nums}"
    # Backstop: guarantee room for the collision suffix even when nums alone is long.
    base = base[: max_length - _SUFFIX_HEADROOM]
    candidate, suffix = base, 1
    # id is the StudySession primary key (globally unique, NOT group-scoped).
    # Best-effort pre-check; the PK constraint on the caller's INSERT is the real guard.
    while StudySession.objects.filter(id=candidate).exists():
        suffix += 1
        if suffix > _MAX_SUFFIX:
            raise RuntimeError(f"Could not generate a unique session id for base {base!r}")
        candidate = f"{base}-{suffix}"
    return candidate
