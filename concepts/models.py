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

    def __str__(self):
        return f"{self.group} / {self.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "name"], name="uniq_concept_per_group"),
        ]
        ordering = ["name"]
