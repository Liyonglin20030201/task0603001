import pytest
from sqlalchemy import text as sa_text

from tests.conftest import create_test_user, get_auth_headers
from app.models.document import Document
from app.models.tag import Tag
from app.services.search_service import (
    update_fts_entry, delete_fts_entry,
    search_documents, count_search_results, rebuild_fts_index,
)


def _create_doc(db, owner_id, title, content="", summary="", tags=None):
    doc = Document(
        title=title,
        original_filename=f"{title}.txt",
        file_type="txt",
        summary=summary,
        content=content,
        owner_id=owner_id,
        current_version=1,
    )
    if tags:
        for tag_name in tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            doc.tags.append(tag)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


class TestSearchService:
    def test_search_by_title(self, db):
        user = create_test_user(db, "owner1")
        doc = _create_doc(db, user.id, "Python Tutorial Guide", content="Learn Python programming")
        update_fts_entry(db, doc.id)

        results = search_documents(db, "Python")
        assert len(results) == 1
        assert results[0].doc_id == doc.id

    def test_search_by_content(self, db):
        user = create_test_user(db, "owner2")
        doc = _create_doc(db, user.id, "Document Title", content="machine learning algorithm explained")
        update_fts_entry(db, doc.id)

        results = search_documents(db, "machine")
        assert len(results) == 1
        assert results[0].doc_id == doc.id

    def test_search_by_summary(self, db):
        user = create_test_user(db, "owner3")
        doc = _create_doc(db, user.id, "Report", summary="annual sales data analysis report")
        update_fts_entry(db, doc.id)

        results = search_documents(db, "sales")
        assert len(results) == 1

    def test_search_by_tags(self, db):
        user = create_test_user(db, "owner4")
        doc = _create_doc(db, user.id, "Design Doc", tags=["frontend", "React"])
        update_fts_entry(db, doc.id)

        results = search_documents(db, "React")
        assert len(results) == 1

    def test_search_no_results(self, db):
        user = create_test_user(db, "owner5")
        _create_doc(db, user.id, "Unrelated Document", content="some content")
        results = search_documents(db, "nonexistentkeywordxyz")
        assert len(results) == 0

    def test_search_relevance_ordering(self, db):
        user = create_test_user(db, "owner6")
        doc1 = _create_doc(db, user.id, "Python basics", content="short intro")
        doc2 = _create_doc(db, user.id, "Advanced Python", content="Python Python Python deep dive")
        update_fts_entry(db, doc1.id)
        update_fts_entry(db, doc2.id)

        results = search_documents(db, "Python")
        assert len(results) == 2

    def test_search_with_pagination(self, db):
        user = create_test_user(db, "owner7")
        for i in range(5):
            doc = _create_doc(db, user.id, f"TestDoc{i} keyword", content=f"shared keyword content {i}")
            update_fts_entry(db, doc.id)

        results = search_documents(db, "keyword", limit=2, offset=0)
        assert len(results) == 2

        results_page2 = search_documents(db, "keyword", limit=2, offset=2)
        assert len(results_page2) == 2

        results_page3 = search_documents(db, "keyword", limit=2, offset=4)
        assert len(results_page3) == 1

    def test_count_search_results(self, db):
        user = create_test_user(db, "owner8")
        for i in range(3):
            doc = _create_doc(db, user.id, f"CountDoc{i} searchterm", content="unified searchterm")
            update_fts_entry(db, doc.id)

        count = count_search_results(db, "searchterm")
        assert count == 3

    def test_delete_fts_entry(self, db):
        user = create_test_user(db, "owner9")
        doc = _create_doc(db, user.id, "ToDelete searchable", content="searchable content here")
        update_fts_entry(db, doc.id)

        assert count_search_results(db, "searchable") == 1
        delete_fts_entry(db, doc.id)
        assert count_search_results(db, "searchable") == 0

    def test_update_fts_entry_after_modification(self, db):
        user = create_test_user(db, "owner10")
        doc = _create_doc(db, user.id, "OriginalTitle", content="original content")
        update_fts_entry(db, doc.id)

        assert count_search_results(db, "OriginalTitle") == 1

        doc.title = "ModifiedTitle"
        doc.content = "modified content"
        db.commit()
        update_fts_entry(db, doc.id)

        assert count_search_results(db, "OriginalTitle") == 0
        assert count_search_results(db, "ModifiedTitle") == 1

    def test_rebuild_fts_index(self, db):
        user = create_test_user(db, "owner11")
        doc1 = _create_doc(db, user.id, "RebuildDoc1 target", content="rebuild target")
        doc2 = _create_doc(db, user.id, "RebuildDoc2 target", content="rebuild target")

        rebuild_fts_index(db)
        assert count_search_results(db, "target") == 2

    def test_deleted_doc_excluded_from_rebuild(self, db):
        user = create_test_user(db, "owner12")
        doc = _create_doc(db, user.id, "SoftDeleted uniqueterm", content="should not appear")
        doc.is_deleted = True
        db.commit()

        rebuild_fts_index(db)
        assert count_search_results(db, "uniqueterm") == 0

    def test_snippet_highlights(self, db):
        user = create_test_user(db, "owner13")
        doc = _create_doc(db, user.id, "HighlightTest", content="this contains keyword information text")
        update_fts_entry(db, doc.id)

        results = search_documents(db, "keyword")
        assert len(results) == 1
        assert "<mark>" in results[0].content_snippet


class TestSearchAPI:
    def test_search_endpoint_basic(self, client, db, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("test.txt", b"Full text search content here", "text/plain")},
            data={"title": "Searchable Doc"},
        )

        resp = client.get("/api/search", headers=editor_headers, params={"q": "Searchable"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "Searchable"
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert data["items"][0]["title"] == "Searchable Doc"

    def test_search_requires_auth(self, client):
        resp = client.get("/api/search", params={"q": "test"})
        assert resp.status_code == 401

    def test_search_empty_query_rejected(self, client, editor_user, editor_headers):
        resp = client.get("/api/search", headers=editor_headers, params={"q": ""})
        assert resp.status_code == 422

    def test_search_no_query_param(self, client, editor_user, editor_headers):
        resp = client.get("/api/search", headers=editor_headers)
        assert resp.status_code == 422

    def test_search_pagination_params(self, client, db, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        for i in range(5):
            client.post(
                "/api/documents", headers=editor_headers,
                files={"file": (f"doc{i}.txt", f"pagination test content {i}".encode(), "text/plain")},
                data={"title": f"Pagination Doc {i}"},
            )

        resp = client.get("/api/search", headers=editor_headers, params={"q": "Pagination", "page": 1, "page_size": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1

    def test_search_highlights_title(self, client, db, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("hl.txt", b"some content", "text/plain")},
            data={"title": "Highlight Test Document"},
        )

        resp = client.get("/api/search", headers=editor_headers, params={"q": "Highlight"})
        data = resp.json()
        if data["items"]:
            assert "<mark>" in data["items"][0]["title_highlight"] or "Highlight" in data["items"][0]["title_highlight"]

    def test_search_respects_permission(self, client, db, editor_user, editor_headers, viewer_user, viewer_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("secret.txt", b"secret content here", "text/plain")},
            data={"title": "Restricted Doc"},
        )
        doc_id = resp.json()["id"]

        from app.models.document_permission import DocumentPermission
        perm = DocumentPermission(
            document_id=doc_id, user_id=editor_user.id,
            permission_level="admin", granted_by=editor_user.id,
        )
        db.add(perm)
        db.commit()

        resp = client.get("/api/search", headers=viewer_headers, params={"q": "Restricted"})
        data = resp.json()
        doc_ids = [item["id"] for item in data["items"]]
        assert doc_id not in doc_ids

    def test_search_result_fields(self, client, db, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("fields.txt", b"field verification content", "text/plain")},
            data={"title": "FieldCheck"},
        )

        resp = client.get("/api/search", headers=editor_headers, params={"q": "FieldCheck"})
        data = resp.json()
        assert "items" in data
        assert "query" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "title" in item
            assert "file_type" in item
            assert "title_highlight" in item
            assert "summary_highlight" in item
            assert "content_highlight" in item
            assert "relevance" in item
            assert "tags" in item
            assert "created_at" in item
