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

    def __str__(self):
        return f"{self.book} #{self.problem_number}"
