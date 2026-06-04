import pytest

from app.models.document import Document
from app.models.project import Project
from app.models.tag import Tag
from app.models.document_permission import DocumentPermission


class TestBatchDelete:
    def test_delete_multiple_docs(self, client, editor_headers, editor_user, db):
        docs = []
        for i in range(3):
            doc = Document(
                title=f"Batch Del {i}", original_filename=f"bd{i}.txt", file_type="txt",
                owner_id=editor_user.id, content="content",
            )
            db.add(doc)
            docs.append(doc)
        db.commit()
        for d in docs:
            db.refresh(d)

        resp = client.post(
            "/api/documents/batch/delete",
            json={"document_ids": [d.id for d in docs]},
            headers=editor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["succeeded"] == 3
        assert data["failed"] == 0

        for d in docs:
            db.refresh(d)
            assert d.is_deleted is True

    def test_partial_access(self, client, editor_headers, editor_user, admin_user, db):
        own_doc = Document(
            title="Own Doc", original_filename="own.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        other_doc = Document(
            title="Other Doc", original_filename="other.txt", file_type="txt",
            owner_id=admin_user.id, content="content",
        )
        db.add_all([own_doc, other_doc])
        db.commit()
        db.refresh(own_doc)
        db.refresh(other_doc)

        perm = DocumentPermission(
            document_id=other_doc.id, user_id=admin_user.id,
            permission_level="admin", granted_by=admin_user.id,
        )
        db.add(perm)
        db.commit()

        resp = client.post(
            "/api/documents/batch/delete",
            json={"document_ids": [own_doc.id, other_doc.id]},
            headers=editor_headers,
        )
        data = resp.json()
        assert data["succeeded"] == 1
        assert data["failed"] == 1
        assert data["errors"][0]["document_id"] == other_doc.id

    def test_viewer_forbidden(self, client, viewer_headers):
        resp = client.post(
            "/api/documents/batch/delete",
            json={"document_ids": [1]},
            headers=viewer_headers,
        )
        assert resp.status_code == 403


class TestBatchMove:
    def test_move_to_project(self, client, editor_headers, editor_user, db):
        project = Project(name="Target Project", description="target", created_by=editor_user.id, owner_id=editor_user.id)
        db.add(project)
        db.commit()
        db.refresh(project)

        docs = []
        for i in range(2):
            doc = Document(
                title=f"Move {i}", original_filename=f"m{i}.txt", file_type="txt",
                owner_id=editor_user.id, content="content",
            )
            db.add(doc)
            docs.append(doc)
        db.commit()
        for d in docs:
            db.refresh(d)

        resp = client.post(
            "/api/documents/batch/move",
            json={"document_ids": [d.id for d in docs], "project_id": project.id},
            headers=editor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["succeeded"] == 2

        for d in docs:
            db.refresh(d)
            assert d.project_id == project.id

    def test_nonexistent_project(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Move Doc", original_filename="mv.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.post(
            "/api/documents/batch/move",
            json={"document_ids": [doc.id], "project_id": 9999},
            headers=editor_headers,
        )
        assert resp.status_code == 404


class TestBatchTags:
    def test_add_tags(self, client, editor_headers, editor_user, db):
        docs = []
        for i in range(3):
            doc = Document(
                title=f"Tag {i}", original_filename=f"t{i}.txt", file_type="txt",
                owner_id=editor_user.id, content="content",
            )
            db.add(doc)
            docs.append(doc)
        db.commit()
        for d in docs:
            db.refresh(d)

        resp = client.post(
            "/api/documents/batch/tags",
            json={"document_ids": [d.id for d in docs], "tag_names": ["important", "review"]},
            headers=editor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["succeeded"] == 3

        for d in docs:
            db.refresh(d)
            tag_names = [t.name for t in d.tags]
            assert "important" in tag_names
            assert "review" in tag_names

    def test_creates_new_tags(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="New Tag Doc", original_filename="nt.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.post(
            "/api/documents/batch/tags",
            json={"document_ids": [doc.id], "tag_names": ["brand-new-tag"]},
            headers=editor_headers,
        )
        assert resp.status_code == 200

        tag = db.query(Tag).filter(Tag.name == "brand-new-tag").first()
        assert tag is not None

    def test_idempotent_tag_add(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Idem Doc", original_filename="id.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        for _ in range(2):
            client.post(
                "/api/documents/batch/tags",
                json={"document_ids": [doc.id], "tag_names": ["dup-tag"]},
                headers=editor_headers,
            )

        db.refresh(doc)
        assert sum(1 for t in doc.tags if t.name == "dup-tag") == 1


class TestBatchPermissions:
    def test_admin_sets_permissions(self, client, admin_headers, admin_user, editor_user, db):
        docs = []
        for i in range(2):
            doc = Document(
                title=f"Perm {i}", original_filename=f"p{i}.txt", file_type="txt",
                owner_id=admin_user.id, content="content",
            )
            db.add(doc)
            docs.append(doc)
        db.commit()
        for d in docs:
            db.refresh(d)

        resp = client.post(
            "/api/documents/batch/permissions",
            json={
                "document_ids": [d.id for d in docs],
                "user_id": editor_user.id,
                "permission_level": "read",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["succeeded"] == 2

        for d in docs:
            perm = db.query(DocumentPermission).filter(
                DocumentPermission.document_id == d.id,
                DocumentPermission.user_id == editor_user.id,
            ).first()
            assert perm is not None
            assert perm.permission_level == "read"

    def test_editor_forbidden(self, client, editor_headers, editor_user, db):
        resp = client.post(
            "/api/documents/batch/permissions",
            json={"document_ids": [1], "user_id": editor_user.id, "permission_level": "read"},
            headers=editor_headers,
        )
        assert resp.status_code == 403

    def test_nonexistent_docs_in_errors(self, client, admin_headers, admin_user, editor_user, db):
        doc = Document(
            title="Exists", original_filename="e.txt", file_type="txt",
            owner_id=admin_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.post(
            "/api/documents/batch/permissions",
            json={
                "document_ids": [doc.id, 9999],
                "user_id": editor_user.id,
                "permission_level": "write",
            },
            headers=admin_headers,
        )
        data = resp.json()
        assert data["succeeded"] == 1
        assert data["failed"] == 1
        assert data["errors"][0]["document_id"] == 9999
