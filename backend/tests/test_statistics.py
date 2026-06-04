import pytest
from datetime import datetime, timezone

from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.document_access_log import DocumentAccessLog


class TestSystemStats:
    def test_admin_can_access(self, client, admin_headers, db):
        resp = client.get("/api/statistics/system", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_documents" in data
        assert "total_visits" in data
        assert "total_users" in data
        assert "popular_documents" in data
        assert "active_users" in data

    def test_editor_forbidden(self, client, editor_headers):
        resp = client.get("/api/statistics/system", headers=editor_headers)
        assert resp.status_code == 403

    def test_viewer_forbidden(self, client, viewer_headers):
        resp = client.get("/api/statistics/system", headers=viewer_headers)
        assert resp.status_code == 403

    def test_counts_correct(self, client, admin_headers, admin_user, db):
        doc = Document(
            title="Stats Doc",
            original_filename="stats.txt",
            file_type="txt",
            owner_id=admin_user.id,
            content="test content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        for _ in range(3):
            db.add(DocumentAccessLog(user_id=admin_user.id, document_id=doc.id))
        db.commit()

        resp = client.get("/api/statistics/system", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_documents"] == 1
        assert data["total_visits"] == 3

    def test_popular_documents_ordering(self, client, admin_headers, admin_user, editor_user, db):
        doc_a = Document(
            title="Popular Doc",
            original_filename="a.txt",
            file_type="txt",
            owner_id=admin_user.id,
            content="content a",
        )
        doc_b = Document(
            title="Less Popular Doc",
            original_filename="b.txt",
            file_type="txt",
            owner_id=admin_user.id,
            content="content b",
        )
        db.add_all([doc_a, doc_b])
        db.commit()
        db.refresh(doc_a)
        db.refresh(doc_b)

        for _ in range(5):
            db.add(DocumentAccessLog(user_id=admin_user.id, document_id=doc_a.id))
        for _ in range(2):
            db.add(DocumentAccessLog(user_id=editor_user.id, document_id=doc_b.id))
        db.commit()

        resp = client.get("/api/statistics/system", headers=admin_headers)
        data = resp.json()
        assert len(data["popular_documents"]) == 2
        assert data["popular_documents"][0]["document_id"] == doc_a.id
        assert data["popular_documents"][0]["access_count"] == 5
        assert data["popular_documents"][1]["document_id"] == doc_b.id
        assert data["popular_documents"][1]["access_count"] == 2

    def test_active_users_ordering(self, client, admin_headers, admin_user, editor_user, db):
        doc = Document(
            title="Test Doc",
            original_filename="t.txt",
            file_type="txt",
            owner_id=admin_user.id,
            content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        for _ in range(4):
            db.add(DocumentAccessLog(user_id=editor_user.id, document_id=doc.id))
        db.add(DocumentAccessLog(user_id=admin_user.id, document_id=doc.id))
        db.commit()

        resp = client.get("/api/statistics/system", headers=admin_headers)
        data = resp.json()
        assert len(data["active_users"]) == 2
        assert data["active_users"][0]["user_id"] == editor_user.id
        assert data["active_users"][0]["access_count"] == 4


class TestDocumentStats:
    def test_access_records(self, client, admin_headers, admin_user, editor_user, db):
        doc = Document(
            title="Stats Detail Doc",
            original_filename="d.txt",
            file_type="txt",
            owner_id=admin_user.id,
            content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        db.add(DocumentAccessLog(user_id=admin_user.id, document_id=doc.id))
        db.add(DocumentAccessLog(user_id=editor_user.id, document_id=doc.id))
        db.commit()

        resp = client.get(f"/api/statistics/documents/{doc.id}", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == doc.id
        assert data["total_accesses"] == 2
        assert len(data["access_records"]) == 2

    def test_version_history(self, client, admin_headers, admin_user, db):
        doc = Document(
            title="Version Doc",
            original_filename="v.txt",
            file_type="txt",
            owner_id=admin_user.id,
            content="content",
            current_version=2,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        v1 = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            file_path="/tmp/v1.txt",
            file_size=100,
            uploaded_by=admin_user.id,
        )
        v2 = DocumentVersion(
            document_id=doc.id,
            version_number=2,
            file_path="/tmp/v2.txt",
            file_size=200,
            uploaded_by=admin_user.id,
        )
        db.add_all([v1, v2])
        db.commit()

        resp = client.get(f"/api/statistics/documents/{doc.id}", headers=admin_headers)
        data = resp.json()
        assert len(data["version_history"]) == 2
        assert data["version_history"][0]["version_number"] == 2
        assert data["version_history"][1]["version_number"] == 1

    def test_requires_read_access(self, client, viewer_headers, editor_user, db):
        from app.models.document_permission import DocumentPermission

        doc = Document(
            title="Private Doc",
            original_filename="p.txt",
            file_type="txt",
            owner_id=editor_user.id,
            content="private",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        perm = DocumentPermission(
            document_id=doc.id,
            user_id=editor_user.id,
            permission_level="admin",
            granted_by=editor_user.id,
        )
        db.add(perm)
        db.commit()

        resp = client.get(f"/api/statistics/documents/{doc.id}", headers=viewer_headers)
        assert resp.status_code == 403

    def test_not_found(self, client, admin_headers):
        resp = client.get("/api/statistics/documents/9999", headers=admin_headers)
        assert resp.status_code == 404

    def test_access_log_created_on_document_view(self, client, admin_headers, admin_user, db):
        doc = Document(
            title="View Doc",
            original_filename="view.txt",
            file_type="txt",
            owner_id=admin_user.id,
            content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        client.get(f"/api/documents/{doc.id}", headers=admin_headers)

        logs = db.query(DocumentAccessLog).filter(DocumentAccessLog.document_id == doc.id).all()
        assert len(logs) == 1
        assert logs[0].user_id == admin_user.id
