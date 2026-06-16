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

def test_str_representations():
    group = StudyGroup.objects.create(name="Alpha", slug="alpha")
    assert str(group) == "Alpha"
    user = User.objects.create_user(email="x@y.com", name="X", password="pw", group=group)
    assert str(user) == "x@y.com"

def test_create_superuser_flags():
    su = User.objects.create_superuser(email="admin@x.com", name="Admin", password="pw")
    assert su.is_staff is True
    assert su.is_superuser is True
