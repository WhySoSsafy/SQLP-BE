import pytest
from rest_framework.test import APIClient
from accounts.models import User
from study.tests.test_validate import PAYLOAD

pytestmark = pytest.mark.django_db


def _make_client(email="a@b.com", name="세은"):
    u = User.objects.create_user(email=email, name=name, password="pw12345")
    c = APIClient()
    c.force_authenticate(u)
    return c, u


def _create_session_and_participant(client):
    resp = client.post("/api/sessions/", PAYLOAD, format="json")
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    detail = client.get(f"/api/sessions/{session_id}/")
    assert detail.status_code == 200
    participant_id = detail.json()["problems"][0]["participants"][0]["id"]
    return participant_id


# ── happy path ──────────────────────────────────────────────────────────────

def test_post_comment_returns_201_with_correct_fields():
    client, user = _make_client()
    participant_id = _create_session_and_participant(client)

    resp = client.post(
        f"/api/participants/{participant_id}/comments/",
        {"content": "좋은 풀이입니다."},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["content"] == "좋은 풀이입니다."
    assert body["author_name"] == "세은"
    assert body["is_mine"] is True
    assert "id" in body
    assert "created_at" in body


def test_get_comment_list_returns_posted_comment():
    client, user = _make_client()
    participant_id = _create_session_and_participant(client)

    client.post(
        f"/api/participants/{participant_id}/comments/",
        {"content": "리스트 확인용"},
        format="json",
    )

    resp = client.get(f"/api/participants/{participant_id}/comments/")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["content"] == "리스트 확인용"


# ── validation ──────────────────────────────────────────────────────────────

def test_blank_content_returns_400():
    client, user = _make_client()
    participant_id = _create_session_and_participant(client)

    resp = client.post(
        f"/api/participants/{participant_id}/comments/",
        {"content": "  "},
        format="json",
    )
    assert resp.status_code == 400


# ── delete own comment ───────────────────────────────────────────────────────

def test_delete_own_comment_returns_ok_and_empties_list():
    client, user = _make_client()
    participant_id = _create_session_and_participant(client)

    post_resp = client.post(
        f"/api/participants/{participant_id}/comments/",
        {"content": "삭제 테스트"},
        format="json",
    )
    assert post_resp.status_code == 201
    comment_id = post_resp.json()["id"]

    del_resp = client.delete(f"/api/comments/{comment_id}/")
    assert del_resp.status_code == 200
    assert del_resp.json() == {"ok": True}

    list_resp = client.get(f"/api/participants/{participant_id}/comments/")
    assert list_resp.status_code == 200
    assert list_resp.json() == []


# ── delete other user's comment → 403 ───────────────────────────────────────

def test_delete_other_users_comment_returns_403():
    """
    Both users share the same default StudyGroup (get_or_create slug='default'),
    so user B can see the comment (not 404) but cannot delete it (403).
    """
    client_a, user_a = _make_client(email="a@b.com", name="세은")
    # user_b must see the same group; create_user assigns the default group to both
    client_b, user_b = _make_client(email="b@b.com", name="수철")
    # sanity: same group
    assert user_a.group_id == user_b.group_id

    participant_id = _create_session_and_participant(client_a)

    post_resp = client_a.post(
        f"/api/participants/{participant_id}/comments/",
        {"content": "A의 댓글"},
        format="json",
    )
    assert post_resp.status_code == 201
    comment_id = post_resp.json()["id"]

    del_resp = client_b.delete(f"/api/comments/{comment_id}/")
    assert del_resp.status_code == 403
    body = del_resp.json()
    assert body["ok"] is False
