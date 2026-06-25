import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.models import ProblemParticipant, Comment
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db


def _client():
    u = User.objects.create_user(email="a@b.com", name="세은", password="pw12345")
    c = APIClient()
    c.force_authenticate(u)
    return c, u


def test_comment_created_and_linked():
    client, author = _client()
    resp = client.post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 201
    participant = ProblemParticipant.objects.first()
    assert participant is not None

    comment = Comment.objects.create(
        participant=participant,
        author=author,
        content="테스트 코멘트입니다.",
    )

    assert participant.comments.count() == 1
    saved = participant.comments.first()
    assert saved.content == "테스트 코멘트입니다."
    assert saved.author == author
    assert saved.created_at is not None


def test_comment_participant_delete_cascades():
    client, author = _client()
    resp = client.post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 201
    participant = ProblemParticipant.objects.first()

    Comment.objects.create(
        participant=participant,
        author=author,
        content="삭제될 코멘트",
    )
    assert Comment.objects.count() == 1
    participant.delete()
    assert Comment.objects.count() == 0


def test_comment_author_null_on_user_delete():
    client, author = _client()
    resp = client.post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 201
    participant = ProblemParticipant.objects.first()

    Comment.objects.create(
        participant=participant,
        author=author,
        content="작성자 삭제 테스트",
    )
    comment_pk = Comment.objects.first().pk
    author.delete()
    comment = Comment.objects.get(pk=comment_pk)
    assert comment.author is None
    assert comment.content == "작성자 삭제 테스트"
