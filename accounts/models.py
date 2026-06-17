from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
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
