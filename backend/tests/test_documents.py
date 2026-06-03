import os
from tests.conftest import create_test_user, get_auth_headers


def test_upload_pdf_as_editor(client, editor_user, editor_headers, sample_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

    response = client.post(
        "/api/documents",
        headers=editor_headers,
        files={"file": ("test.pdf", sample_pdf, "application/pdf")},
        data={"title": "Test Document"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["file_type"] == "pdf"
    assert data["current_version"] == 1


def test_upload_rejected_for_viewer(client, viewer_user, viewer_headers, sample_pdf):
    response = client.post(
        "/api/documents",
        headers=viewer_headers,
        files={"file": ("test.pdf", sample_pdf, "application/pdf")},
        data={"title": "Test Document"},
    )
    assert response.status_code == 403


def test_upload_invalid_file_type(client, editor_user, editor_headers):
    response = client.post(
        "/api/documents",
        headers=editor_headers,
        files={"file": ("test.exe", b"hello", "application/octet-stream")},
        data={"title": "Test Document"},
    )
    assert response.status_code == 422


def test_upload_txt_file(client, editor_user, editor_headers, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

    response = client.post(
        "/api/documents",
        headers=editor_headers,
        files={"file": ("readme.txt", b"Hello this is a text file with content", "text/plain")},
        data={"title": "Text File"},
    )
    assert response.status_code == 201
    assert response.json()["file_type"] == "txt"


def test_list_documents(client, editor_user, editor_headers, sample_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

    client.post("/api/documents", headers=editor_headers, files={"file": ("t1.pdf", sample_pdf, "application/pdf")}, data={"title": "Doc 1"})
    client.post("/api/documents", headers=editor_headers, files={"file": ("t2.pdf", sample_pdf, "application/pdf")}, data={"title": "Doc 2"})

    response = client.get("/api/documents", headers=editor_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_soft_delete_and_restore(client, admin_user, admin_headers, sample_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

    resp = client.post("/api/documents", headers=admin_headers, files={"file": ("t.pdf", sample_pdf, "application/pdf")}, data={"title": "To Delete"})
    doc_id = resp.json()["id"]

    assert client.delete(f"/api/documents/{doc_id}", headers=admin_headers).status_code == 204

    list_resp = client.get("/api/documents", headers=admin_headers)
    assert list_resp.json()["total"] == 0

    trash_resp = client.get("/api/documents/trash", headers=admin_headers)
    assert len(trash_resp.json()) == 1

    restore_resp = client.post(f"/api/documents/{doc_id}/restore", headers=admin_headers)
    assert restore_resp.status_code == 200
    assert restore_resp.json()["is_deleted"] == False


def test_version_rollback(client, editor_user, editor_headers, sample_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

    resp = client.post("/api/documents", headers=editor_headers, files={"file": ("t.pdf", sample_pdf, "application/pdf")}, data={"title": "Versioned"})
    doc_id = resp.json()["id"]
    assert resp.json()["current_version"] == 1

    v2_resp = client.post(f"/api/documents/{doc_id}/versions", headers=editor_headers, files={"file": ("t2.pdf", sample_pdf, "application/pdf")})
    assert v2_resp.status_code == 201

    doc_resp = client.get(f"/api/documents/{doc_id}", headers=editor_headers)
    assert doc_resp.json()["current_version"] == 2

    rollback_resp = client.post(f"/api/documents/{doc_id}/versions/1/rollback", headers=editor_headers)
    assert rollback_resp.status_code == 200
    assert rollback_resp.json()["current_version"] == 1


def test_rollback_nonexistent_version(client, editor_user, editor_headers, sample_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

    resp = client.post("/api/documents", headers=editor_headers, files={"file": ("t.pdf", sample_pdf, "application/pdf")}, data={"title": "V1 Only"})
    doc_id = resp.json()["id"]

    rollback_resp = client.post(f"/api/documents/{doc_id}/versions/99/rollback", headers=editor_headers)
    assert rollback_resp.status_code == 404
