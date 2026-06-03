from tests.conftest import create_test_user, get_auth_headers
from app.models.document import Document


def _create_doc(db, owner_id):
    doc = Document(
        title="Permission Test Doc",
        original_filename="test.pdf",
        file_type="pdf",
        owner_id=owner_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_admin_can_manage_users(client, admin_user, admin_headers, editor_user):
    response = client.get("/api/users", headers=admin_headers)
    assert response.status_code == 200

    response = client.put(f"/api/users/{editor_user.id}/role", headers=admin_headers, json={"role": "admin"})
    assert response.status_code == 200


def test_editor_cannot_manage_users(client, editor_user, editor_headers):
    response = client.get("/api/users", headers=editor_headers)
    assert response.status_code == 403


def test_viewer_cannot_upload(client, viewer_user, viewer_headers):
    response = client.post(
        "/api/documents",
        headers=viewer_headers,
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Should Fail"},
    )
    assert response.status_code == 403


def test_editor_cannot_restore(client, db, admin_user, admin_headers, editor_user, editor_headers):
    doc = _create_doc(db, admin_user.id)
    doc.is_deleted = True
    db.commit()

    response = client.post(f"/api/documents/{doc.id}/restore", headers=editor_headers)
    assert response.status_code == 403


def test_viewer_can_list_and_comment(client, db, editor_user, viewer_user, viewer_headers):
    doc = _create_doc(db, editor_user.id)

    response = client.get("/api/documents", headers=viewer_headers)
    assert response.status_code == 200

    response = client.post(f"/api/documents/{doc.id}/comments", headers=viewer_headers, json={"content": "Viewer note"})
    assert response.status_code == 201


def test_document_permission_grant_and_access(client, db, editor_user, editor_headers, viewer_user, viewer_headers):
    doc = _create_doc(db, editor_user.id)

    grant_resp = client.post(
        f"/api/documents/{doc.id}/permissions",
        headers=editor_headers,
        json={"user_id": viewer_user.id, "permission_level": "read"},
    )
    assert grant_resp.status_code == 201

    perms_resp = client.get(f"/api/documents/{doc.id}/permissions", headers=editor_headers)
    assert len(perms_resp.json()) == 1

    access_resp = client.get(f"/api/documents/{doc.id}", headers=viewer_headers)
    assert access_resp.status_code == 200


def test_document_permission_denied_when_not_granted(client, db, editor_user, editor_headers, viewer_user, viewer_headers, admin_user):
    doc = _create_doc(db, editor_user.id)

    other_user = create_test_user(db, "other_viewer", "viewer")
    client.post(f"/api/documents/{doc.id}/permissions", headers=editor_headers, json={"user_id": other_user.id, "permission_level": "read"})

    access_resp = client.get(f"/api/documents/{doc.id}", headers=viewer_headers)
    assert access_resp.status_code == 403


def test_revoke_permission(client, db, editor_user, editor_headers, viewer_user):
    doc = _create_doc(db, editor_user.id)

    grant_resp = client.post(f"/api/documents/{doc.id}/permissions", headers=editor_headers, json={"user_id": viewer_user.id, "permission_level": "write"})
    perm_id = grant_resp.json()["id"]

    revoke_resp = client.delete(f"/api/documents/{doc.id}/permissions/{perm_id}", headers=editor_headers)
    assert revoke_resp.status_code == 204

    perms_resp = client.get(f"/api/documents/{doc.id}/permissions", headers=editor_headers)
    assert len(perms_resp.json()) == 0
