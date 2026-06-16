# SQLP Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Django REST backend for an SQLP study group — recording study sessions and serving derived analytics (dashboard, weak concepts, review recommendations, calendar, growth reports) across the 20 endpoints in `api.md`.

**Architecture:** Django 5 + DRF. Custom email User in a single auto-assigned StudyGroup. Normalized relational models (Session → Problem → ProblemParticipant, plus Concept and ProblemAnalysis). All analytics computed on-the-fly via ORM aggregation isolated in `services/` modules. All data queries scoped to `request.user.group`. A custom DRF exception handler renders the common error envelope.

**Tech Stack:** Django 5, djangorestframework, djangorestframework-simplejwt, psycopg(3), django-environ, pytest-django, factory_boy, PostgreSQL.

**Spec:** `docs/superpowers/specs/2026-06-16-sqlp-backend-design.md`

**Per-task workflow (subagent + codex):** Each task ends with a commit. After each task, the subagent's work is verified with codex before the next task starts. Tasks are ordered so each builds only on committed prior tasks.

---

## Phase 0 — Project Scaffold

### Task 0.1: Python project + dependencies

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `.env.example`

- [ ] **Step 1: Write `requirements.txt`**

```
Django==5.0.6
djangorestframework==3.15.1
djangorestframework-simplejwt==5.3.1
psycopg[binary]==3.1.19
django-environ==0.11.2
pytest==8.2.0
pytest-django==4.8.0
factory_boy==3.3.0
```

- [ ] **Step 2: Write `pytest.ini`**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.dev
python_files = tests.py test_*.py *_tests.py
addopts = -v
```

- [ ] **Step 3: Write `.env.example`**

```
DJANGO_SECRET_KEY=dev-insecure-change-me
DJANGO_DEBUG=True
DATABASE_URL=postgres://sqlp:sqlp@localhost:5432/sqlp
```

- [ ] **Step 4: Create venv and install**

Run: `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
Expected: installs succeed.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pytest.ini .env.example
git commit -m "chore: add python dependencies and pytest config"
```

### Task 0.2: Django project + split settings

**Files:**
- Create: `manage.py`
- Create: `config/__init__.py`, `config/urls.py`, `config/wsgi.py`, `config/asgi.py`
- Create: `config/settings/__init__.py`, `config/settings/base.py`, `config/settings/dev.py`, `config/settings/prod.py`

- [ ] **Step 1: Scaffold project**

Run: `. .venv/bin/activate && django-admin startproject config .`
Then move generated `config/settings.py` content into the split layout below (delete the single `settings.py`).

- [ ] **Step 2: Write `config/settings/base.py`**

```python
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(DJANGO_DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "study",
    "concepts",
    "analytics",
    "common",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

DATABASES = {"default": env.db("DATABASE_URL")}

AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
}

# Scoring constants (overridable)
UNDERSTANDING_SCORE = {"모름": 0, "애매": 50, "이해": 100}
SCORE_UNDERSTANDING_WEIGHT = 0.7
SCORE_CORRECT_WEIGHT = 0.3
WEAK_THRESHOLD = 50
```

- [ ] **Step 3: Write `config/settings/dev.py` and `prod.py`**

```python
# dev.py
from .base import *  # noqa
DEBUG = True
```
```python
# prod.py
from .base import *  # noqa
DEBUG = False
```

- [ ] **Step 4: Create empty app packages**

Run: `. .venv/bin/activate && for a in accounts study concepts analytics common; do python manage.py startapp $a; done`

- [ ] **Step 5: Verify Django boots**

Run: `. .venv/bin/activate && python manage.py check`
Expected: "System check identified no issues" (creating apps may require AUTH_USER_MODEL to exist — if check fails on missing User model, proceed to Task 1.1 first, then re-run).

- [ ] **Step 6: Commit**

```bash
git add manage.py config accounts study concepts analytics common
git commit -m "chore: scaffold django project with split settings and apps"
```

---

## Phase 1 — Accounts & Auth

### Task 1.1: StudyGroup + custom User model

**Files:**
- Create: `accounts/models.py`
- Create: `accounts/managers.py`
- Test: `accounts/tests/test_models.py`, `accounts/tests/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# accounts/tests/test_models.py
import pytest
from accounts.models import User, StudyGroup

pytestmark = pytest.mark.django_db

def test_create_user_assigns_default_group():
    user = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    assert user.email == "a@b.com"
    assert user.check_password("pw12345")
    assert user.group is not None
    assert user.profile_label == ""

def test_default_group_is_shared():
    u1 = User.objects.create_user(email="a@b.com", name="세은", password="pw")
    u2 = User.objects.create_user(email="c@d.com", name="수철", password="pw")
    assert u1.group_id == u2.group_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest accounts/tests/test_models.py -v`
Expected: FAIL (cannot import User / model not defined).

- [ ] **Step 3: Write `accounts/managers.py`**

```python
from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, name, password, **extra):
        if not email:
            raise ValueError("email is required")
        from accounts.models import StudyGroup
        group = extra.pop("group", None) or StudyGroup.get_default()
        user = self.model(email=self.normalize_email(email), name=name, group=group, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, name, password, **extra)

    def create_superuser(self, email, name, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create(email, name, password, **extra)
```

- [ ] **Step 4: Write `accounts/models.py`**

```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from accounts.managers import UserManager

class StudyGroup(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)

    DEFAULT_SLUG = "default"

    @classmethod
    def get_default(cls):
        group, _ = cls.objects.get_or_create(
            slug=cls.DEFAULT_SLUG, defaults={"name": "기본 스터디"}
        )
        return group

    def __str__(self):
        return self.name

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=50)
    profile_label = models.CharField(max_length=100, blank=True, default="")
    group = models.ForeignKey(StudyGroup, on_delete=models.PROTECT, related_name="members")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email
```

- [ ] **Step 5: Make migrations and run test**

Run: `. .venv/bin/activate && python manage.py makemigrations accounts && pytest accounts/tests/test_models.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add accounts/ config/settings/base.py
git commit -m "feat(accounts): custom email user with auto-assigned default group"
```

### Task 1.2: Register endpoint

**Files:**
- Create: `accounts/serializers.py`
- Create: `accounts/views.py`
- Create: `accounts/urls.py`
- Modify: `config/urls.py`
- Test: `accounts/tests/test_auth.py`

- [ ] **Step 1: Write the failing test**

```python
# accounts/tests/test_auth.py
import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

def test_register_creates_user():
    client = APIClient()
    resp = client.post("/api/auth/register/", {
        "name": "세은", "email": "seun@example.com", "password": "password123"
    }, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert body["user"]["email"] == "seun@example.com"
    assert "id" in body["user"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest accounts/tests/test_auth.py::test_register_creates_user -v`
Expected: FAIL (404, URL not wired).

- [ ] **Step 3: Write `accounts/serializers.py`**

```python
from rest_framework import serializers
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "profile_label"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["name", "email", "password"]

    def create(self, validated):
        return User.objects.create_user(**validated)
```

- [ ] **Step 4: Write `accounts/views.py`**

```python
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.serializers import RegisterSerializer, UserSerializer, MeSerializer

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"ok": True, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
```

- [ ] **Step 5: Write `accounts/urls.py` and wire `config/urls.py`**

```python
# accounts/urls.py
from django.urls import path
from accounts.views import RegisterView, MeView
from accounts.jwt import LoginView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("users/me/", MeView.as_view()),
]
```
```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("accounts.urls")),
    path("api/", include("study.urls")),
    path("api/", include("concepts.urls")),
    path("api/", include("analytics.urls")),
]
```

> Note: `accounts/urls.py` imports `LoginView` from `accounts.jwt` (Task 1.3) and study/concepts/analytics urls (later tasks). Create empty `urls.py` with `urlpatterns = []` in `study`, `concepts`, `analytics` now so includes resolve. Comment out the `accounts.jwt` import line until Task 1.3 if running this task in isolation.

- [ ] **Step 6: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest accounts/tests/test_auth.py::test_register_creates_user -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add accounts config/urls.py study/urls.py concepts/urls.py analytics/urls.py
git commit -m "feat(accounts): register and me endpoints"
```

### Task 1.3: Login (JWT) endpoint

**Files:**
- Create: `accounts/jwt.py`
- Test: `accounts/tests/test_auth.py` (add)

- [ ] **Step 1: Write the failing test (append)**

```python
def test_login_returns_tokens_and_user():
    from accounts.models import User
    User.objects.create_user(email="seun@example.com", name="세은", password="password123")
    client = APIClient()
    resp = client.post("/api/auth/login/", {
        "email": "seun@example.com", "password": "password123"
    }, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert "access" in body and "refresh" in body
    assert body["user"]["email"] == "seun@example.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest accounts/tests/test_auth.py::test_login_returns_tokens_and_user -v`
Expected: FAIL (cannot import accounts.jwt).

- [ ] **Step 3: Write `accounts/jwt.py`**

```python
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from accounts.serializers import UserSerializer

class LoginSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
```

Ensure `accounts/urls.py` import line for `LoginView` is active.

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest accounts/tests/test_auth.py -v`
Expected: PASS (all auth tests).

- [ ] **Step 5: Add SimpleJWT settings to `config/settings/base.py`**

```python
from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
```

- [ ] **Step 6: Commit**

```bash
git add accounts config/settings/base.py
git commit -m "feat(accounts): JWT login returning access/refresh/user"
```

---

## Phase 2 — Common Error Envelope

### Task 2.1: Custom exception handler

**Files:**
- Create: `common/exceptions.py`
- Create: `common/codes.py`
- Test: `common/tests/test_exceptions.py`, `common/tests/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# common/tests/test_exceptions.py
import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

def test_validation_error_envelope():
    client = APIClient()
    resp = client.post("/api/auth/register/", {"email": "bad"}, format="json")
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["code"] == "VALIDATION_ERROR"
    assert isinstance(body["errors"], list)
    assert "path" in body["errors"][0] and "message" in body["errors"][0]

def test_auth_failure_envelope():
    client = APIClient()
    resp = client.get("/api/users/me/")
    assert resp.status_code in (401, 403)
    assert resp.json()["ok"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest common/tests/test_exceptions.py -v`
Expected: FAIL (errors envelope not applied / import error).

- [ ] **Step 3: Write `common/codes.py`**

```python
VALIDATION_ERROR = "VALIDATION_ERROR"
DUPLICATE_SESSION = "DUPLICATE_SESSION"
NOT_FOUND = "NOT_FOUND"
AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
PERMISSION_DENIED = "PERMISSION_DENIED"
```

- [ ] **Step 4: Write `common/exceptions.py`**

```python
from rest_framework.views import exception_handler
from rest_framework import exceptions
from common import codes

def _flatten(detail, prefix="$"):
    out = []
    if isinstance(detail, dict):
        for key, val in detail.items():
            out += _flatten(val, f"{prefix}.{key}")
    elif isinstance(detail, list):
        scalar = [d for d in detail if not isinstance(d, (dict, list))]
        for d in scalar:
            out.append({"path": prefix, "message": str(d)})
        for i, d in enumerate(detail):
            if isinstance(d, (dict, list)):
                out += _flatten(d, f"{prefix}[{i}]")
    else:
        out.append({"path": prefix, "message": str(detail)})
    return out

def _code_for(exc):
    if isinstance(exc, exceptions.ValidationError):
        return codes.VALIDATION_ERROR
    if isinstance(exc, exceptions.NotFound):
        return codes.NOT_FOUND
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        return codes.AUTHENTICATION_FAILED
    if isinstance(exc, exceptions.PermissionDenied):
        return codes.PERMISSION_DENIED
    return getattr(exc, "default_code", "ERROR").upper()

def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    code = _code_for(exc)
    if isinstance(exc, exceptions.ValidationError):
        message = "입력값이 올바르지 않습니다."
        errors = _flatten(exc.detail)
    else:
        message = str(getattr(exc, "detail", "오류가 발생했습니다."))
        errors = []
    response.data = {"ok": False, "code": code, "message": message, "errors": errors}
    return response
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest common/tests/test_exceptions.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add common
git commit -m "feat(common): unified error envelope exception handler"
```

---

## Phase 3 — Study Sessions

### Task 3.1: Study models

**Files:**
- Create: `study/models.py`
- Test: `study/tests/test_models.py`, `study/tests/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# study/tests/test_models.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest study/tests/test_models.py -v`
Expected: FAIL (import error).

- [ ] **Step 3: Write `study/models.py`**

```python
from django.contrib.postgres.fields import ArrayField
from django.db import models
from accounts.models import StudyGroup
from concepts.models import Concept

UNDERSTANDING_CHOICES = [("모름", "모름"), ("애매", "애매"), ("이해", "이해")]

class StudySession(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="sessions")
    session_date = models.DateField()
    book = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-session_date", "-created_at"]

class Problem(models.Model):
    id = models.CharField(primary_key=True, max_length=300)
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="problems")
    problem_number = models.IntegerField()
    subject_area = models.CharField(max_length=100)
    solution_summary = models.TextField(blank=True, default="")
    concepts = models.ManyToManyField(Concept, related_name="problems", blank=True)

    class Meta:
        ordering = ["problem_number"]

class ProblemParticipant(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="participants")
    name = models.CharField(max_length=50)
    member = models.ForeignKey("accounts.User", null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="participations")
    is_correct = models.BooleanField(default=False)
    understanding = models.CharField(max_length=4, choices=UNDERSTANDING_CHOICES)
    concepts_covered = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    concepts_missed = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    errors = ArrayField(models.TextField(), default=list, blank=True)
    review_required = models.BooleanField(default=False)
    done = models.BooleanField(default=False)

    @property
    def wrong_answer_id(self):
        return f"{self.problem_id}-{self.name}"
```

> `Concept` is imported from `concepts.models` (Task 5.1). Implement Task 5.1 BEFORE this task, or temporarily replace the M2M target with `"concepts.Concept"` string and ensure the concepts app + model exist first. Recommended order: do Task 5.1, then this task.

- [ ] **Step 4: Make migrations and run test**

Run: `. .venv/bin/activate && python manage.py makemigrations study && pytest study/tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add study
git commit -m "feat(study): session/problem/participant models"
```

### Task 3.2: Slug generation service

**Files:**
- Create: `study/services/__init__.py`, `study/services/slug.py`
- Test: `study/tests/test_slug.py`

- [ ] **Step 1: Write the failing test**

```python
# study/tests/test_slug.py
import pytest
from accounts.models import StudyGroup
from study.models import StudySession
from study.services.slug import build_session_id

pytestmark = pytest.mark.django_db

def test_slug_format():
    g = StudyGroup.get_default()
    sid = build_session_id(g, "2026-06-13", "SQLP 실전문제", [1, 2])
    assert sid == "2026-06-13-sqlp-실전문제-1-2"

def test_slug_collision_suffix():
    g = StudyGroup.get_default()
    StudySession.objects.create(id="2026-06-13-sqlp-실전문제-1", group=g,
                                session_date="2026-06-13", book="SQLP 실전문제")
    sid = build_session_id(g, "2026-06-13", "SQLP 실전문제", [1])
    assert sid == "2026-06-13-sqlp-실전문제-1-2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest study/tests/test_slug.py -v`
Expected: FAIL (import error).

- [ ] **Step 3: Write `study/services/slug.py`**

```python
from django.utils.text import slugify
from study.models import StudySession

def build_session_id(group, session_date, book, problem_numbers):
    book_slug = slugify(book, allow_unicode=True)
    nums = "-".join(str(n) for n in sorted(problem_numbers))
    base = f"{session_date}-{book_slug}-{nums}"
    candidate, suffix = base, 1
    while StudySession.objects.filter(group=group, id=candidate).exists():
        suffix += 1
        candidate = f"{base}-{suffix}"
    return candidate
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest study/tests/test_slug.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add study/services
git commit -m "feat(study): session slug id builder with collision suffix"
```

### Task 3.3: Scoring service

**Files:**
- Create: `study/services/scoring.py`
- Test: `study/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# study/tests/test_scoring.py
from study.services.scoring import participant_score, average_understanding

def test_participant_score_correct_understood():
    # 이해(100)*0.7 + correct(100)*0.3 = 100
    assert participant_score("이해", True) == 100

def test_participant_score_unknown_wrong():
    # 모름(0)*0.7 + 0*0.3 = 0
    assert participant_score("모름", False) == 0

def test_participant_score_ambiguous_correct():
    # 애매(50)*0.7 + 100*0.3 = 65
    assert participant_score("애매", True) == 65

def test_average_understanding_rounds():
    assert average_understanding([100, 0]) == 50
    assert average_understanding([]) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest study/tests/test_scoring.py -v`
Expected: FAIL (import error).

- [ ] **Step 3: Write `study/services/scoring.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest study/tests/test_scoring.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add study/services/scoring.py
git commit -m "feat(study): participant scoring formula service"
```

### Task 3.4: Validate endpoint (#4) + input serializers

**Files:**
- Create: `study/serializers.py`
- Create: `study/views.py`
- Create/Modify: `study/urls.py`
- Test: `study/tests/test_validate.py`

- [ ] **Step 1: Write the failing test**

```python
# study/tests/test_validate.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User

pytestmark = pytest.mark.django_db

PAYLOAD = {
    "session_date": "2026-06-13", "book": "SQLP 실전문제",
    "speakers": ["세은", "수철"],
    "problems": [{
        "problem_number": 1, "subject_area": "SQL 기본 및 활용",
        "concepts": ["JOIN", "OUTER JOIN"], "solution_summary": "요약",
        "participants": [{
            "name": "세은", "is_correct": True, "understanding": "애매",
            "concepts_covered": ["OUTER JOIN"], "concepts_missed": ["NULL 처리"],
            "errors": ["기준 테이블 방향 혼동"], "review_required": True
        }],
    }],
}

def _auth_client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_validate_ok_returns_preview():
    resp = _auth_client().post("/api/analysis/validate/", PAYLOAD, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["preview"]["problemCount"] == 1
    assert body["preview"]["participantCount"] == 2
    assert set(body["preview"]["conceptTags"]) == {"JOIN", "OUTER JOIN"}

def test_validate_bad_understanding_fails():
    bad = {**PAYLOAD}
    bad["problems"][0]["participants"][0]["understanding"] = "최고"
    resp = _auth_client().post("/api/analysis/validate/", bad, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest study/tests/test_validate.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `study/serializers.py`**

```python
from rest_framework import serializers
from study.models import UNDERSTANDING_CHOICES

UNDERSTANDING_VALUES = [c[0] for c in UNDERSTANDING_CHOICES]

class ParticipantInputSerializer(serializers.Serializer):
    name = serializers.CharField()
    is_correct = serializers.BooleanField()
    understanding = serializers.ChoiceField(choices=UNDERSTANDING_VALUES)
    concepts_covered = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    concepts_missed = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    errors = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    review_required = serializers.BooleanField(default=False)

class ProblemInputSerializer(serializers.Serializer):
    problem_number = serializers.IntegerField()
    subject_area = serializers.CharField()
    concepts = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    solution_summary = serializers.CharField(required=False, allow_blank=True, default="")
    participants = ParticipantInputSerializer(many=True)

class SessionInputSerializer(serializers.Serializer):
    session_date = serializers.DateField()
    book = serializers.CharField()
    speakers = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    problems = ProblemInputSerializer(many=True)
```

- [ ] **Step 4: Write `study/views.py` (validate) and `study/urls.py`**

```python
# study/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from study.serializers import SessionInputSerializer

class ValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SessionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        concept_tags = []
        for p in data["problems"]:
            for c in p["concepts"]:
                if c not in concept_tags:
                    concept_tags.append(c)
        participants = {pp["name"] for p in data["problems"] for pp in p["participants"]}
        preview = {
            "sessionDate": str(data["session_date"]),
            "book": data["book"],
            "problemCount": len(data["problems"]),
            "participantCount": len(participants | set(data["speakers"])),
            "conceptTags": concept_tags,
        }
        return Response({"ok": True, "preview": preview})
```
```python
# study/urls.py
from django.urls import path
from study.views import ValidateView

urlpatterns = [
    path("analysis/validate/", ValidateView.as_view()),
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest study/tests/test_validate.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add study
git commit -m "feat(study): analysis validate endpoint with input serializers"
```

### Task 3.5: Session create service + endpoint (#5)

**Files:**
- Create: `study/services/session_create.py`
- Modify: `study/views.py`, `study/urls.py`
- Test: `study/tests/test_session_create.py`

- [ ] **Step 1: Write the failing test**

```python
# study/tests/test_session_create.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c, u

def test_create_session_returns_slug():
    c, _ = _client()
    resp = c.post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert body["session_id"] == "2026-06-13-sqlp-실전문제-1"

def test_duplicate_session_rejected():
    c, _ = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 409
    assert resp.json()["code"] == "DUPLICATE_SESSION"

def test_participant_linked_to_member_by_name():
    c, u = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    from study.models import ProblemParticipant
    pp = ProblemParticipant.objects.get(name="세은")
    assert pp.member_id == u.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest study/tests/test_session_create.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `study/services/session_create.py`**

```python
from django.db import transaction
from rest_framework.exceptions import APIException
from rest_framework import status
from accounts.models import User
from concepts.models import Concept
from study.models import StudySession, Problem, ProblemParticipant
from study.services.slug import build_session_id

class DuplicateSession(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = ("같은 날짜, 문제집명, 문제번호 구성을 가진 학습 세션이 "
                      "이미 저장되어 있습니다.")
    default_code = "DUPLICATE_SESSION"

def _base_session_id(group, data, numbers):
    from django.utils.text import slugify
    book_slug = slugify(data["book"], allow_unicode=True)
    nums = "-".join(str(n) for n in sorted(numbers))
    return f"{data['session_date']}-{book_slug}-{nums}"

@transaction.atomic
def create_session(group, data):
    numbers = [p["problem_number"] for p in data["problems"]]
    base_id = _base_session_id(group, data, numbers)
    if StudySession.objects.filter(group=group, id=base_id).exists():
        raise DuplicateSession()
    session_id = build_session_id(group, str(data["session_date"]), data["book"], numbers)
    session = StudySession.objects.create(
        id=session_id, group=group,
        session_date=data["session_date"], book=data["book"],
    )
    members = {u.name: u for u in User.objects.filter(group=group)}
    for p in data["problems"]:
        problem = Problem.objects.create(
            id=f"{session_id}-p{p['problem_number']}", session=session,
            problem_number=p["problem_number"], subject_area=p["subject_area"],
            solution_summary=p.get("solution_summary", ""),
        )
        for cname in p["concepts"]:
            concept, _ = Concept.objects.get_or_create(
                group=group, name=cname,
                defaults={"subject": p["subject_area"]},
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
```

- [ ] **Step 4: Add create view + url**

```python
# append to study/views.py
from rest_framework import status
from study.services.session_create import create_session

class SessionCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SessionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = create_session(request.user.group, serializer.validated_data)
        return Response({"ok": True, "session_id": session.id},
                        status=status.HTTP_201_CREATED)
```
```python
# add to study/urls.py urlpatterns
path("sessions/", SessionCreateListView.as_view()),
```
(import `SessionCreateListView` in urls.)

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest study/tests/test_session_create.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add study
git commit -m "feat(study): create session endpoint with dedup and member linking"
```

### Task 3.6: Session list (#6) with filters + derived aggregates

**Files:**
- Modify: `study/views.py`, `study/urls.py`
- Create: `study/services/serialize.py`
- Test: `study/tests/test_session_list.py`

- [ ] **Step 1: Write the failing test**

```python
# study/tests/test_session_list.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_list_returns_summary_fields():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/sessions/")
    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["book"] == "SQLP 실전문제"
    assert row["problem_count"] == 1
    assert row["review_required_count"] == 1
    assert "average_understanding" in row
    assert set(row["speakers"]) >= {"세은"}

def test_list_search_filters_by_book():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    assert len(c.get("/api/sessions/?search=SQLP").json()) == 1
    assert len(c.get("/api/sessions/?search=없는책").json()) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest study/tests/test_session_list.py -v`
Expected: FAIL (GET not implemented / wrong shape).

- [ ] **Step 3: Write `study/services/serialize.py`**

```python
from study.services.scoring import participant_score, average_understanding

def session_summary(session):
    participants = []
    speakers = set()
    review_required = 0
    for problem in session.problems.all():
        for pp in problem.participants.all():
            participants.append(participant_score(pp.understanding, pp.is_correct))
            speakers.add(pp.name)
            if pp.review_required:
                review_required += 1
    return {
        "id": session.id,
        "session_date": str(session.session_date),
        "book": session.book,
        "speakers": sorted(speakers),
        "problem_count": session.problems.count(),
        "average_understanding": average_understanding(participants),
        "review_required_count": review_required,
        "created_at": session.created_at.isoformat().replace("+00:00", "Z"),
    }
```

- [ ] **Step 4: Implement list in `SessionCreateListView.get`**

```python
# append to study/views.py
from study.models import StudySession
from study.services.serialize import session_summary

class SessionCreateListView(APIView):  # extend the existing class
    # ... keep existing post ...
    def get(self, request):
        qs = (StudySession.objects.filter(group=request.user.group)
              .prefetch_related("problems__participants"))
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(book__icontains=search)
        date_from = request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(session_date__gte=date_from)
        date_to = request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(session_date__lte=date_to)
        rows = [session_summary(s) for s in qs]
        understanding = request.query_params.get("understanding")
        if understanding == "high":
            rows = [r for r in rows if r["average_understanding"] >= 70]
        elif understanding == "low":
            rows = [r for r in rows if r["average_understanding"] < 50]
        return Response(rows)
```

> Implementation note: merge `get` into the existing `SessionCreateListView` from Task 3.5 — do not create a second class. Keep the `post` method intact.

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest study/tests/test_session_list.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add study
git commit -m "feat(study): session list with filters and derived aggregates"
```

### Task 3.7: Session detail (#7) + delete (#8)

**Files:**
- Modify: `study/views.py`, `study/urls.py`, `study/services/serialize.py`
- Test: `study/tests/test_session_detail.py`

- [ ] **Step 1: Write the failing test**

```python
# study/tests/test_session_detail.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_detail_returns_nested_problems():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    resp = c.get(f"/api/sessions/{sid}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == sid
    assert body["problems"][0]["problem_number"] == 1
    assert body["problems"][0]["participants"][0]["name"] == "세은"

def test_delete_session():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    resp = c.delete(f"/api/sessions/{sid}/")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert c.get(f"/api/sessions/{sid}/").status_code == 404

def test_detail_other_group_404():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    from accounts.models import StudyGroup
    other = StudyGroup.objects.create(name="other", slug="other")
    u2 = User.objects.create_user(email="z@z.com", name="other", password="pw12345", group=other)
    c2 = APIClient(); c2.force_authenticate(u2)
    assert c2.get(f"/api/sessions/{sid}/").status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest study/tests/test_session_detail.py -v`
Expected: FAIL (404 route missing).

- [ ] **Step 3: Add `session_detail` to `study/services/serialize.py`**

```python
def session_detail(session):
    problems = []
    for problem in session.problems.all():
        problems.append({
            "id": problem.id,
            "problem_number": problem.problem_number,
            "subject_area": problem.subject_area,
            "concepts": [c.name for c in problem.concepts.all()],
            "solution_summary": problem.solution_summary,
            "participants": [{
                "name": pp.name,
                "is_correct": pp.is_correct,
                "understanding": pp.understanding,
                "concepts_covered": pp.concepts_covered,
                "concepts_missed": pp.concepts_missed,
                "errors": pp.errors,
                "review_required": pp.review_required,
            } for pp in problem.participants.all()],
        })
    speakers = sorted({pp.name for p in session.problems.all() for pp in p.participants.all()})
    return {
        "id": session.id,
        "session_date": str(session.session_date),
        "book": session.book,
        "speakers": speakers,
        "created_at": session.created_at.isoformat().replace("+00:00", "Z"),
        "problems": problems,
    }
```

- [ ] **Step 4: Add detail/delete view + url**

```python
# append to study/views.py
from django.shortcuts import get_object_or_404
from study.services.serialize import session_detail

class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, session_id):
        return get_object_or_404(
            StudySession.objects.filter(group=request.user.group)
            .prefetch_related("problems__participants", "problems__concepts"),
            id=session_id,
        )

    def get(self, request, session_id):
        return Response(session_detail(self._get(request, session_id)))

    def delete(self, request, session_id):
        self._get(request, session_id).delete()
        return Response({"ok": True})
```
```python
# add to study/urls.py
path("sessions/<str:session_id>/", SessionDetailView.as_view()),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest study/tests/test_session_detail.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add study
git commit -m "feat(study): session detail and delete with group scoping"
```

### Task 3.8: Wrong-answers list (#12) + complete toggle (#13)

**Files:**
- Modify: `study/views.py`, `study/urls.py`
- Create: `study/services/wrong_answers.py`
- Test: `study/tests/test_wrong_answers.py`

- [ ] **Step 1: Write the failing test**

```python
# study/tests/test_wrong_answers.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_wrong_answers_list():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/wrong-answers/")
    assert resp.status_code == 200
    item = resp.json()[0]
    assert item["person"] == "세은"
    assert item["reviewRequired"] is True
    assert item["done"] is False
    assert item["problemNumber"] == 1

def test_mark_done():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    wid = c.get("/api/wrong-answers/").json()[0]["id"]
    resp = c.patch(f"/api/wrong-answers/{wid}/", {"done": True}, format="json")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "id": wid, "done": True}
    assert c.get("/api/wrong-answers/").json()[0]["done"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest study/tests/test_wrong_answers.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `study/services/wrong_answers.py`**

```python
from django.db.models import Q
from study.models import ProblemParticipant

def wrong_answer_queryset(group):
    return (ProblemParticipant.objects
            .filter(problem__session__group=group)
            .filter(Q(review_required=True) | Q(is_correct=False))
            .select_related("problem", "problem__session")
            .prefetch_related("problem__concepts"))

def serialize_wrong_answer(pp):
    problem, session = pp.problem, pp.problem.session
    return {
        "id": pp.wrong_answer_id,
        "sessionId": session.id,
        "problemId": problem.id,
        "problemNumber": problem.problem_number,
        "sessionDate": str(session.session_date),
        "book": session.book,
        "person": pp.name,
        "concepts": [c.name for c in problem.concepts.all()],
        "understanding": pp.understanding,
        "missed": pp.concepts_missed,
        "errors": pp.errors,
        "explanation": problem.solution_summary,
        "isCorrect": pp.is_correct,
        "reviewRequired": pp.review_required,
        "done": pp.done,
    }
```

- [ ] **Step 4: Add views + urls**

```python
# append to study/views.py
from rest_framework.exceptions import NotFound
from study.models import ProblemParticipant
from study.services.wrong_answers import wrong_answer_queryset, serialize_wrong_answer

class WrongAnswerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = wrong_answer_queryset(request.user.group)
        return Response([serialize_wrong_answer(pp) for pp in qs])

class WrongAnswerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, wrong_answer_id):
        for pp in wrong_answer_queryset(request.user.group):
            if pp.wrong_answer_id == wrong_answer_id:
                pp.done = bool(request.data.get("done", pp.done))
                pp.save(update_fields=["done"])
                return Response({"ok": True, "id": wrong_answer_id, "done": pp.done})
        raise NotFound("오답노트를 찾을 수 없습니다.")
```
```python
# add to study/urls.py
path("wrong-answers/", WrongAnswerListView.as_view()),
path("wrong-answers/<str:wrong_answer_id>/", WrongAnswerDetailView.as_view()),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest study/tests/test_wrong_answers.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add study
git commit -m "feat(study): wrong-answers list and complete toggle"
```

---

## Phase 4 — Concepts

### Task 5.1: Concept model

> **Order note:** Implement this BEFORE Task 3.1 (study models import Concept).

**Files:**
- Create: `concepts/models.py`
- Test: `concepts/tests/test_models.py`, `concepts/tests/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# concepts/tests/test_models.py
import pytest
from accounts.models import StudyGroup
from concepts.models import Concept

pytestmark = pytest.mark.django_db

def test_concept_unique_per_group():
    g = StudyGroup.get_default()
    Concept.objects.create(group=g, name="OUTER JOIN", subject="SQL 기본 및 활용")
    with pytest.raises(Exception):
        Concept.objects.create(group=g, name="OUTER JOIN", subject="SQL 기본 및 활용")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest concepts/tests/test_models.py -v`
Expected: FAIL (import error).

- [ ] **Step 3: Write `concepts/models.py`**

```python
from django.contrib.postgres.fields import ArrayField
from django.db import models
from accounts.models import StudyGroup

class Concept(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="concepts")
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    frequent_question_types = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    confusing_points = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    wrong_patterns = ArrayField(models.CharField(max_length=200), default=list, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "name"], name="uniq_concept_per_group"),
        ]
        ordering = ["name"]
```

- [ ] **Step 4: Make migrations and run test**

Run: `. .venv/bin/activate && python manage.py makemigrations concepts && pytest concepts/tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add concepts
git commit -m "feat(concepts): concept model unique per group"
```

### Task 5.2: Concept understanding service

**Files:**
- Create: `concepts/services.py`, `concepts/__init__.py` (if missing)
- Test: `concepts/tests/test_services.py`

- [ ] **Step 1: Write the failing test**

```python
# concepts/tests/test_services.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User, StudyGroup
from concepts.models import Concept
from concepts.services import concept_understanding
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def test_concept_understanding_aggregates_participants():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u)
    c.post("/api/sessions/", PAYLOAD, format="json")
    concept = Concept.objects.get(group=u.group, name="OUTER JOIN")
    score = concept_understanding(concept)
    assert 0 <= score <= 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest concepts/tests/test_services.py -v`
Expected: FAIL (import error).

- [ ] **Step 3: Write `concepts/services.py`**

```python
from study.services.scoring import participant_score, average_understanding

def _participants_for_concept(concept):
    from study.models import ProblemParticipant
    return ProblemParticipant.objects.filter(problem__concepts=concept)

def concept_understanding(concept):
    scores = [participant_score(pp.understanding, pp.is_correct)
              for pp in _participants_for_concept(concept)]
    return average_understanding(scores)

def concept_review_recommended(concept, threshold=50):
    return concept_understanding(concept) < threshold
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest concepts/tests/test_services.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add concepts
git commit -m "feat(concepts): concept understanding aggregation service"
```

### Task 5.3: Concept list (#16) + detail (#17)

**Files:**
- Create: `concepts/views.py`, `concepts/urls.py`
- Test: `concepts/tests/test_views.py`

- [ ] **Step 1: Write the failing test**

```python
# concepts/tests/test_views.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_concept_list():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/concepts/")
    assert resp.status_code == 200
    names = {item["name"] for item in resp.json()}
    assert "OUTER JOIN" in names
    item = next(i for i in resp.json() if i["name"] == "OUTER JOIN")
    assert "myUnderstanding" in item and "reviewRecommended" in item

def test_concept_detail():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    cid = c.get("/api/concepts/").json()[0]["id"]
    resp = c.get(f"/api/concepts/{cid}/")
    assert resp.status_code == 200
    body = resp.json()
    assert "relatedProblems" in body
    assert "frequentQuestionTypes" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest concepts/tests/test_views.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `concepts/views.py` and `concepts/urls.py`**

```python
# concepts/views.py
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from concepts.models import Concept
from concepts.services import concept_understanding, concept_review_recommended

class ConceptListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        out = []
        for c in Concept.objects.filter(group=request.user.group):
            out.append({
                "id": c.id, "name": c.name, "subject": c.subject, "summary": c.summary,
                "myUnderstanding": concept_understanding(c),
                "reviewRecommended": concept_review_recommended(c),
            })
        return out_response(out)

def out_response(data):
    return Response(data)

class ConceptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, concept_id):
        c = get_object_or_404(Concept, group=request.user.group, id=concept_id)
        related = []
        from study.models import ProblemParticipant
        for pp in ProblemParticipant.objects.filter(
            problem__concepts=c, problem__session__group=request.user.group
        ).select_related("problem", "problem__session"):
            related.append({
                "sessionId": pp.problem.session_id,
                "problemNumber": pp.problem.problem_number,
                "understanding": pp.understanding,
                "reviewRequired": pp.review_required,
            })
        return Response({
            "id": c.id, "name": c.name, "subject": c.subject, "summary": c.summary,
            "frequentQuestionTypes": c.frequent_question_types,
            "confusingPoints": c.confusing_points,
            "wrongPatterns": c.wrong_patterns,
            "relatedProblems": related,
            "myUnderstanding": concept_understanding(c),
            "reviewRecommended": concept_review_recommended(c),
        })
```
```python
# concepts/urls.py
from django.urls import path
from concepts.views import ConceptListView, ConceptDetailView

urlpatterns = [
    path("concepts/", ConceptListView.as_view()),
    path("concepts/<int:concept_id>/", ConceptDetailView.as_view()),
]
```

> Cleanup: replace the `out_response` helper with a direct `return Response(out)` in `ConceptListView.get` — it exists only to make the diff explicit. Final code should just `return Response(out)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest concepts/tests/test_views.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add concepts
git commit -m "feat(concepts): concept list and detail endpoints"
```

---

## Phase 5 — Analytics

### Task 6.1: Weak concepts (#11) service + endpoint

**Files:**
- Create: `analytics/services/__init__.py`, `analytics/services/weak_concepts.py`
- Create: `analytics/views.py`, `analytics/urls.py`
- Test: `analytics/tests/test_weak_concepts.py`, `analytics/tests/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
# analytics/tests/test_weak_concepts.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_weak_concepts_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/weak-concepts/")
    assert resp.status_code == 200
    item = resp.json()[0]
    for key in ("name", "subject", "totalProblems", "weakCountByParticipant",
                "scoreByParticipant", "averageScore", "recommend"):
        assert key in item
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest analytics/tests/test_weak_concepts.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `analytics/services/weak_concepts.py`**

```python
from collections import defaultdict
from concepts.models import Concept
from study.models import ProblemParticipant
from study.services.scoring import participant_score, average_understanding

def weak_concepts(group):
    result = []
    for concept in Concept.objects.filter(group=group):
        pps = list(ProblemParticipant.objects.filter(
            problem__concepts=concept, problem__session__group=group
        ).select_related("problem", "problem__session"))
        if not pps:
            continue
        scores_by_person = defaultdict(list)
        weak_by_person = defaultdict(int)
        last_date = None
        problem_ids = set()
        for pp in pps:
            problem_ids.add(pp.problem_id)
            score = participant_score(pp.understanding, pp.is_correct)
            scores_by_person[pp.name].append(score)
            if pp.review_required or not pp.is_correct:
                weak_by_person[pp.name] += 1
            d = pp.problem.session.session_date
            last_date = d if last_date is None or d > last_date else last_date
        score_by_person = {n: average_understanding(s) for n, s in scores_by_person.items()}
        avg = average_understanding([s for ss in scores_by_person.values() for s in ss])
        result.append({
            "name": concept.name,
            "subject": concept.subject,
            "totalProblems": len(problem_ids),
            "weakCountByParticipant": dict(weak_by_person),
            "scoreByParticipant": score_by_person,
            "averageScore": avg,
            "lastReviewDate": str(last_date) if last_date else None,
            "recommend": avg < 50,
        })
    result.sort(key=lambda x: x["averageScore"])
    return result
```

- [ ] **Step 4: Write `analytics/views.py` and `analytics/urls.py`**

```python
# analytics/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from analytics.services.weak_concepts import weak_concepts

class WeakConceptsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(weak_concepts(request.user.group))
```
```python
# analytics/urls.py
from django.urls import path
from analytics.views import WeakConceptsView

urlpatterns = [
    path("weak-concepts/", WeakConceptsView.as_view()),
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest analytics/tests/test_weak_concepts.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add analytics
git commit -m "feat(analytics): weak concepts endpoint"
```

### Task 6.2: Review recommendations (#10)

**Files:**
- Create: `analytics/services/recommendations.py`
- Modify: `analytics/views.py`, `analytics/urls.py`
- Test: `analytics/tests/test_recommendations.py`

- [ ] **Step 1: Write the failing test**

```python
# analytics/tests/test_recommendations.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_recommendations_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/recommendations/review/")
    assert resp.status_code == 200
    if resp.json():
        item = resp.json()[0]
        for key in ("concept", "subject", "reason", "score"):
            assert key in item
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest analytics/tests/test_recommendations.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `analytics/services/recommendations.py`**

```python
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
```

- [ ] **Step 4: Add view + url**

```python
# append to analytics/views.py
from analytics.services.recommendations import review_recommendations

class ReviewRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(review_recommendations(request.user.group))
```
```python
# add to analytics/urls.py
path("recommendations/review/", ReviewRecommendationsView.as_view()),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest analytics/tests/test_recommendations.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add analytics
git commit -m "feat(analytics): review recommendations endpoint"
```

### Task 6.3: Dashboard summary (#9)

**Files:**
- Create: `analytics/services/dashboard.py`
- Modify: `analytics/views.py`, `analytics/urls.py`
- Test: `analytics/tests/test_dashboard.py`

- [ ] **Step 1: Write the failing test**

```python
# analytics/tests/test_dashboard.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_dashboard_summary_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/dashboard/summary/")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("weeklyProblemCount", "reviewRequiredCount", "averageUnderstanding",
                "studyStreak", "recommendations", "recentSessions"):
        assert key in body
    assert isinstance(body["recommendations"], list)
    assert isinstance(body["recentSessions"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest analytics/tests/test_dashboard.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `analytics/services/dashboard.py`**

```python
from datetime import timedelta
from django.utils import timezone
from study.models import StudySession, Problem, ProblemParticipant
from study.services.scoring import participant_score, average_understanding
from study.services.serialize import session_summary
from analytics.services.recommendations import review_recommendations

def _study_streak(group):
    dates = list(StudySession.objects.filter(group=group)
                 .values_list("session_date", flat=True).distinct().order_by("-session_date"))
    if not dates:
        return 0
    today = timezone.now().date()
    streak, cursor = 0, today
    dateset = set(dates)
    # allow streak to start today or yesterday
    if cursor not in dateset:
        cursor = cursor - timedelta(days=1)
    while cursor in dateset:
        streak += 1
        cursor -= timedelta(days=1)
    return streak

def dashboard_summary(group):
    week_ago = timezone.now().date() - timedelta(days=7)
    weekly_problems = Problem.objects.filter(
        session__group=group, session__session_date__gte=week_ago).count()
    review_required = ProblemParticipant.objects.filter(
        problem__session__group=group, review_required=True).count()
    all_scores = [participant_score(pp.understanding, pp.is_correct)
                  for pp in ProblemParticipant.objects.filter(problem__session__group=group)]
    recent = StudySession.objects.filter(group=group).prefetch_related(
        "problems__participants")[:5]
    recent_out = []
    for s in recent:
        summ = session_summary(s)
        recent_out.append({
            "id": summ["id"], "date": summ["session_date"], "book": summ["book"],
            "problemCount": summ["problem_count"],
            "averageUnderstanding": summ["average_understanding"],
        })
    return {
        "weeklyProblemCount": weekly_problems,
        "reviewRequiredCount": review_required,
        "averageUnderstanding": average_understanding(all_scores),
        "studyStreak": _study_streak(group),
        "recommendations": review_recommendations(group, limit=5),
        "recentSessions": recent_out,
    }
```

- [ ] **Step 4: Add view + url**

```python
# append to analytics/views.py
from analytics.services.dashboard import dashboard_summary

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(dashboard_summary(request.user.group))
```
```python
# add to analytics/urls.py
path("dashboard/summary/", DashboardSummaryView.as_view()),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest analytics/tests/test_dashboard.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add analytics
git commit -m "feat(analytics): dashboard summary endpoint"
```

### Task 6.4: Calendar (#14)

**Files:**
- Create: `analytics/services/calendar.py`
- Modify: `analytics/views.py`, `analytics/urls.py`
- Test: `analytics/tests/test_calendar.py`

- [ ] **Step 1: Write the failing test**

```python
# analytics/tests/test_calendar.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_calendar_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/calendar/?year=2026&month=6")
    assert resp.status_code == 200
    body = resp.json()
    assert body["year"] == 2026 and body["month"] == 6
    assert isinstance(body["days"], list)
    day = next(d for d in body["days"] if d["date"] == "2026-06-13")
    assert day["problemCount"] == 1
    assert "mainConcepts" in day
    assert "monthlyProblemCount" in body and "weeklyProblemCount" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest analytics/tests/test_calendar.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `analytics/services/calendar.py`**

```python
from collections import defaultdict
from datetime import timedelta
from django.utils import timezone
from study.models import StudySession
from study.services.scoring import participant_score, average_understanding

def calendar_data(group, year, month):
    sessions = (StudySession.objects.filter(
        group=group, session_date__year=year, session_date__month=month)
        .prefetch_related("problems__participants", "problems__concepts"))
    by_day = defaultdict(lambda: {"problems": 0, "scores": [], "concepts": defaultdict(int),
                                  "review": 0})
    for s in sessions:
        bucket = by_day[str(s.session_date)]
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
        main = sorted(b["concepts"], key=lambda k: -b["concepts"][k])[:3]
        days.append({
            "date": date, "problemCount": b["problems"],
            "averageUnderstanding": average_understanding(b["scores"]),
            "mainConcepts": main, "reviewRequiredCount": b["review"],
        })
    monthly = sum(d["problemCount"] for d in days)
    week_ago = timezone.now().date() - timedelta(days=7)
    weekly = sum(d["problemCount"] for d in days if d["date"] >= str(week_ago))
    streak_dates = set(by_day.keys())
    return {
        "year": year, "month": month, "days": days,
        "weeklyProblemCount": weekly, "monthlyProblemCount": monthly,
        "studyStreak": len(streak_dates),
    }
```

> Note: `studyStreak` here reflects distinct study days in the month, sufficient for the calendar view. The dashboard's streak (Task 6.3) is the authoritative consecutive-day streak.

- [ ] **Step 4: Add view + url**

```python
# append to analytics/views.py
from analytics.services.calendar import calendar_data

class CalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        year = int(request.query_params.get("year", now.year))
        month = int(request.query_params.get("month", now.month))
        return Response(calendar_data(request.user.group, year, month))
```
Add `from django.utils import timezone` at top of `analytics/views.py`.
```python
# add to analytics/urls.py
path("calendar/", CalendarView.as_view()),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest analytics/tests/test_calendar.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add analytics
git commit -m "feat(analytics): study calendar endpoint"
```

### Task 6.5: Study comparison (#15)

**Files:**
- Create: `analytics/services/comparison.py`
- Modify: `analytics/views.py`, `analytics/urls.py`
- Test: `analytics/tests/test_comparison.py`

- [ ] **Step 1: Write the failing test**

```python
# analytics/tests/test_comparison.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_comparison_shape():
    c = _client()
    sid = c.post("/api/sessions/", PAYLOAD, format="json").json()["session_id"]
    resp = c.get(f"/api/study-comparison/?session_id={sid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sessionId"] == sid
    assert isinstance(body["participants"], list)
    p = body["participants"][0]
    for key in ("name", "averageUnderstanding", "correctCount",
                "reviewRequiredCount", "weakConcepts"):
        assert key in p
    assert "problems" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest analytics/tests/test_comparison.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `analytics/services/comparison.py`**

```python
from collections import defaultdict
from django.shortcuts import get_object_or_404
from study.models import StudySession
from study.services.scoring import participant_score, average_understanding

def study_comparison(group, session_id):
    session = get_object_or_404(
        StudySession.objects.filter(group=group)
        .prefetch_related("problems__participants", "problems__concepts"),
        id=session_id,
    )
    per = defaultdict(lambda: {"scores": [], "correct": 0, "review": 0, "weak": set()})
    problems_out = []
    for problem in session.problems.all():
        p_participants = []
        for pp in problem.participants.all():
            agg = per[pp.name]
            agg["scores"].append(participant_score(pp.understanding, pp.is_correct))
            if pp.is_correct:
                agg["correct"] += 1
            if pp.review_required:
                agg["review"] += 1
            for missed in pp.concepts_missed:
                agg["weak"].add(missed)
            if pp.review_required or not pp.is_correct:
                for c in problem.concepts.all():
                    agg["weak"].add(c.name)
            p_participants.append({
                "name": pp.name, "isCorrect": pp.is_correct,
                "understanding": pp.understanding, "reviewRequired": pp.review_required,
            })
        problems_out.append({
            "problemNumber": problem.problem_number,
            "concepts": [c.name for c in problem.concepts.all()],
            "participants": p_participants,
        })
    participants = [{
        "name": name,
        "averageUnderstanding": average_understanding(v["scores"]),
        "correctCount": v["correct"],
        "reviewRequiredCount": v["review"],
        "weakConcepts": sorted(v["weak"]),
    } for name, v in per.items()]
    return {
        "sessionId": session.id, "book": session.book,
        "sessionDate": str(session.session_date),
        "participants": participants, "problems": problems_out,
    }
```

- [ ] **Step 4: Add view + url**

```python
# append to analytics/views.py
from rest_framework.exceptions import ValidationError
from analytics.services.comparison import study_comparison

class StudyComparisonView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            raise ValidationError({"session_id": ["필수 값입니다."]})
        return Response(study_comparison(request.user.group, session_id))
```
```python
# add to analytics/urls.py
path("study-comparison/", StudyComparisonView.as_view()),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest analytics/tests/test_comparison.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add analytics
git commit -m "feat(analytics): study comparison endpoint"
```

### Task 6.6: Problem analysis register (#18) + list (#19)

**Files:**
- Create: `analytics/models.py`
- Create: `analytics/serializers.py`
- Modify: `analytics/views.py`, `analytics/urls.py`
- Test: `analytics/tests/test_problem_analysis.py`

- [ ] **Step 1: Write the failing test**

```python
# analytics/tests/test_problem_analysis.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

PA = {
    "book": "SQLP 실전문제",
    "problems": [{
        "problem_number": 1, "subject_area": "SQL 기본 및 활용",
        "concepts": ["JOIN", "OUTER JOIN"], "estimated_difficulty": "중",
        "frequency": "높음", "priority": 1
    }],
}

def test_register_and_list():
    c = _client()
    resp = c.post("/api/problem-analysis/", PA, format="json")
    assert resp.status_code == 201
    assert resp.json() == {"ok": True, "created_count": 1}
    listed = c.get("/api/problem-analysis/")
    assert listed.status_code == 200
    item = listed.json()[0]
    assert item["book"] == "SQLP 실전문제"
    assert item["estimated_difficulty"] == "중"
    assert item["concepts"] == ["JOIN", "OUTER JOIN"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest analytics/tests/test_problem_analysis.py -v`
Expected: FAIL (404 / model missing).

- [ ] **Step 3: Write `analytics/models.py`**

```python
from django.contrib.postgres.fields import ArrayField
from django.db import models
from accounts.models import StudyGroup

class ProblemAnalysis(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="problem_analyses")
    book = models.CharField(max_length=200)
    problem_number = models.IntegerField()
    subject_area = models.CharField(max_length=100)
    concepts = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    estimated_difficulty = models.CharField(max_length=10)
    frequency = models.CharField(max_length=20, blank=True, default="")
    priority = models.IntegerField(default=0)

    class Meta:
        ordering = ["priority", "problem_number"]
```

- [ ] **Step 4: Write `analytics/serializers.py`**

```python
from rest_framework import serializers
from analytics.models import ProblemAnalysis

class ProblemAnalysisItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemAnalysis
        fields = ["id", "book", "problem_number", "subject_area", "concepts",
                  "estimated_difficulty", "frequency", "priority"]

class ProblemAnalysisInputSerializer(serializers.Serializer):
    problem_number = serializers.IntegerField()
    subject_area = serializers.CharField()
    concepts = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    estimated_difficulty = serializers.CharField()
    frequency = serializers.CharField(required=False, allow_blank=True, default="")
    priority = serializers.IntegerField(required=False, default=0)

class ProblemAnalysisBulkSerializer(serializers.Serializer):
    book = serializers.CharField()
    problems = ProblemAnalysisInputSerializer(many=True)
```

- [ ] **Step 5: Add view + url, makemigrations**

```python
# append to analytics/views.py
from rest_framework import status
from analytics.models import ProblemAnalysis
from analytics.serializers import (ProblemAnalysisBulkSerializer,
                                   ProblemAnalysisItemSerializer)

class ProblemAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProblemAnalysisBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        objs = [ProblemAnalysis(group=request.user.group, book=data["book"], **p)
                for p in data["problems"]]
        ProblemAnalysis.objects.bulk_create(objs)
        return Response({"ok": True, "created_count": len(objs)},
                        status=status.HTTP_201_CREATED)

    def get(self, request):
        qs = ProblemAnalysis.objects.filter(group=request.user.group)
        return Response(ProblemAnalysisItemSerializer(qs, many=True).data)
```
```python
# add to analytics/urls.py
path("problem-analysis/", ProblemAnalysisView.as_view()),
```
Run: `. .venv/bin/activate && python manage.py makemigrations analytics`

- [ ] **Step 6: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest analytics/tests/test_problem_analysis.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add analytics
git commit -m "feat(analytics): problem analysis register and list"
```

### Task 6.7: Growth report (#20)

**Files:**
- Create: `analytics/services/reports.py`
- Modify: `analytics/views.py`, `analytics/urls.py`
- Test: `analytics/tests/test_reports.py`

- [ ] **Step 1: Write the failing test**

```python
# analytics/tests/test_reports.py
import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db

def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient(); c.force_authenticate(u); return c

def test_growth_report_shape():
    c = _client()
    c.post("/api/sessions/", PAYLOAD, format="json")
    resp = c.get("/api/reports/growth/?period=monthly")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("period", "problemCount", "averageUnderstanding",
                "reviewRequiredCount", "improvedConcepts", "stillWeakConcepts", "trend"):
        assert key in body
    assert body["period"] == "monthly"
    assert isinstance(body["trend"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest analytics/tests/test_reports.py -v`
Expected: FAIL (404).

- [ ] **Step 3: Write `analytics/services/reports.py`**

```python
from collections import defaultdict
from study.models import Problem, ProblemParticipant
from study.services.scoring import participant_score, average_understanding
from analytics.services.weak_concepts import weak_concepts

def growth_report(group, period="monthly"):
    problems = Problem.objects.filter(session__group=group)
    pps = list(ProblemParticipant.objects.filter(problem__session__group=group)
               .select_related("problem", "problem__session"))
    all_scores = [participant_score(pp.understanding, pp.is_correct) for pp in pps]
    review_required = sum(1 for pp in pps if pp.review_required)

    by_date = defaultdict(list)
    for pp in pps:
        by_date[str(pp.problem.session.session_date)].append(
            participant_score(pp.understanding, pp.is_correct))
    trend = [{"date": d, "averageUnderstanding": average_understanding(s)}
             for d, s in sorted(by_date.items())]

    weak = weak_concepts(group)
    still_weak = [w["name"] for w in weak if w["averageScore"] < 50]
    improved = [w["name"] for w in weak if w["averageScore"] >= 70]
    return {
        "period": period,
        "problemCount": problems.count(),
        "averageUnderstanding": average_understanding(all_scores),
        "reviewRequiredCount": review_required,
        "improvedConcepts": improved,
        "stillWeakConcepts": still_weak,
        "trend": trend,
    }
```

- [ ] **Step 4: Add view + url**

```python
# append to analytics/views.py
from analytics.services.reports import growth_report

class GrowthReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "monthly")
        return Response(growth_report(request.user.group, period))
```
```python
# add to analytics/urls.py
path("reports/growth/", GrowthReportView.as_view()),
```

- [ ] **Step 5: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest analytics/tests/test_reports.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add analytics
git commit -m "feat(analytics): growth report endpoint"
```

---

## Phase 6 — Final Integration

### Task 7.1: Full migration + suite + admin smoke

**Files:**
- Modify: `accounts/admin.py` (register models, optional)
- Test: full suite

- [ ] **Step 1: Run full migrations on a clean DB**

Run: `. .venv/bin/activate && python manage.py makemigrations && python manage.py migrate`
Expected: all migrations apply with no errors.

- [ ] **Step 2: Run the full test suite**

Run: `. .venv/bin/activate && pytest -v`
Expected: all tests PASS.

- [ ] **Step 3: Manual smoke via runserver (optional)**

Run: `. .venv/bin/activate && python manage.py runserver` and exercise register → login → create session → dashboard with curl/HTTP client. Confirm error envelope on a bad request.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: final migrations and full-suite green"
```

---

## Self-Review (completed by plan author)

**Spec coverage — all 20 endpoints mapped:**
1 login → 1.3 · 2 register → 1.2 · 3 me → 1.2 · 4 validate → 3.4 · 5 create → 3.5 ·
6 list → 3.6 · 7 detail → 3.7 · 8 delete → 3.7 · 9 dashboard → 6.3 · 10 recommendations → 6.2 ·
11 weak-concepts → 6.1 · 12 wrong-answers → 3.8 · 13 wrong-answer patch → 3.8 ·
14 calendar → 6.4 · 15 comparison → 6.5 · 16 concept list → 5.3 · 17 concept detail → 5.3 ·
18 problem-analysis post → 6.6 · 19 problem-analysis get → 6.6 · 20 growth report → 6.7.
Common error envelope → 2.1. Models → 1.1, 3.1, 5.1, 6.6.

**Dependency order note:** Concepts (5.1) must precede study models (3.1) because `study.Problem.concepts` is M2M → `concepts.Concept`. Recommended execution order: 0.1, 0.2, 1.1, 1.2, 1.3, 2.1, **5.1**, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 5.2, 5.3, 6.1–6.7, 7.1.

**Scoring authority:** `api.md` response numbers are illustrative mock data; the formula in `study/services/scoring.py` is authoritative (documented in spec §5).
