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
    speakers = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    dedup_key = models.CharField(max_length=64, null=True, blank=True, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-session_date", "-created_at"]

    def __str__(self):
        return f"{self.session_date} — {self.book}"


class Problem(models.Model):
    id = models.CharField(primary_key=True, max_length=300)
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="problems")
    problem_number = models.IntegerField()
    subject_area = models.CharField(max_length=100)
    solution_summary = models.TextField(blank=True, default="")
    concepts = models.ManyToManyField(Concept, related_name="problems", blank=True)

    class Meta:
        ordering = ["problem_number"]

    def __str__(self):
        return f"{self.session_id} / #{self.problem_number}"


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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["problem", "name"], name="uniq_participant_per_problem"),
        ]

    def __str__(self):
        return f"{self.problem_id} — {self.name}"

    @property
    def wrong_answer_id(self):
        return f"{self.problem_id}::{self.name}"
