import hashlib

from django.db import migrations


def backfill(apps, schema_editor):
    StudySession = apps.get_model("study", "StudySession")
    for s in StudySession.objects.filter(dedup_key__isnull=True):
        numbers = sorted({p.problem_number for p in s.problems.all()})
        raw = f"{s.group_id}|{s.session_date}|{s.book}|{'-'.join(str(n) for n in numbers)}"
        s.dedup_key = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        s.save(update_fields=["dedup_key"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("study", "0003_studysession_dedup_key")]
    operations = [migrations.RunPython(backfill, noop)]
