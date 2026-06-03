from tests.conftest import create_test_user, get_auth_headers
from app.models.document import Document


def _create_doc(db, owner_id):
    doc = Document(
        title="Test Doc",
        original_filename="test.pdf",
        file_type="pdf",
        owner_id=owner_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_add_comment(client, db, editor_user, editor_headers):
    doc = _create_doc(db, editor_user.id)
    response = client.post(
        f"/api/documents/{doc.id}/comments",
        headers=editor_headers,
        json={"content": "Great document!"},
    )
    assert response.status_code == 201
    assert response.json()["content"] == "Great document!"


def test_list_comments(client, db, editor_user, editor_headers):
    doc = _create_doc(db, editor_user.id)
    client.post(f"/api/documents/{doc.id}/comments", headers=editor_headers, json={"content": "Comment 1"})
    client.post(f"/api/documents/{doc.id}/comments", headers=editor_headers, json={"content": "Comment 2"})

    response = client.get(f"/api/documents/{doc.id}/comments", headers=editor_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_edit_own_comment(client, db, editor_user, editor_headers):
    doc = _create_doc(db, editor_user.id)
    resp = client.post(f"/api/documents/{doc.id}/comments", headers=editor_headers, json={"content": "Original"})
    comment_id = resp.json()["id"]

    update_resp = client.put(
        f"/api/documents/{doc.id}/comments/{comment_id}",
        headers=editor_headers,
        json={"content": "Updated"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["content"] == "Updated"


def test_edit_others_comment_denied(client, db, editor_user, editor_headers, viewer_user, viewer_headers):
    doc = _create_doc(db, editor_user.id)
    resp = client.post(f"/api/documents/{doc.id}/comments", headers=editor_headers, json={"content": "Mine"})
    comment_id = resp.json()["id"]

    update_resp = client.put(
        f"/api/documents/{doc.id}/comments/{comment_id}",
        headers=viewer_headers,
        json={"content": "Hacked"},
    )
    assert update_resp.status_code == 403


def test_viewer_can_comment(client, db, editor_user, viewer_user, viewer_headers):
    doc = _create_doc(db, editor_user.id)
    response = client.post(
        f"/api/documents/{doc.id}/comments",
        headers=viewer_headers,
        json={"content": "Viewer comment"},
    )
    assert response.status_code == 201
