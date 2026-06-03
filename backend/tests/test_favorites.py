import pytest

from tests.conftest import create_test_user, get_auth_headers
from app.models.document import Document
from app.models.favorite import Favorite, FavoriteCategory
from app.models.document_access import DocumentAccess


def _create_doc_directly(db, owner_id, title="Test Doc"):
    doc = Document(
        title=title,
        original_filename=f"{title}.txt",
        file_type="txt",
        content="content",
        owner_id=owner_id,
        current_version=1,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


class TestFavoriteCategories:
    def test_create_category(self, client, editor_user, editor_headers):
        resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "工作文档"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "工作文档"
        assert data["count"] == 0
        assert "id" in data
        assert "created_at" in data

    def test_create_duplicate_category(self, client, editor_user, editor_headers):
        client.post("/api/favorites/categories", headers=editor_headers, json={"name": "重复分类"})
        resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "重复分类"})
        assert resp.status_code == 400

    def test_list_categories(self, client, editor_user, editor_headers):
        client.post("/api/favorites/categories", headers=editor_headers, json={"name": "分类A"})
        client.post("/api/favorites/categories", headers=editor_headers, json={"name": "分类B"})

        resp = client.get("/api/favorites/categories", headers=editor_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        names = [c["name"] for c in data]
        assert "分类A" in names
        assert "分类B" in names

    def test_update_category(self, client, editor_user, editor_headers):
        resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "旧名称"})
        cat_id = resp.json()["id"]

        resp = client.put(f"/api/favorites/categories/{cat_id}", headers=editor_headers, json={"name": "新名称"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名称"

    def test_update_nonexistent_category(self, client, editor_user, editor_headers):
        resp = client.put("/api/favorites/categories/9999", headers=editor_headers, json={"name": "x"})
        assert resp.status_code == 404

    def test_delete_category(self, client, editor_user, editor_headers):
        resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "待删除"})
        cat_id = resp.json()["id"]

        resp = client.delete(f"/api/favorites/categories/{cat_id}", headers=editor_headers)
        assert resp.status_code == 204

        resp = client.get("/api/favorites/categories", headers=editor_headers)
        ids = [c["id"] for c in resp.json()]
        assert cat_id not in ids

    def test_delete_category_uncategorizes_favorites(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        cat_resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "临时"})
        cat_id = cat_resp.json()["id"]

        fav_resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id, "category_id": cat_id})
        fav_id = fav_resp.json()["id"]

        client.delete(f"/api/favorites/categories/{cat_id}", headers=editor_headers)

        resp = client.get("/api/favorites", headers=editor_headers)
        for fav in resp.json():
            if fav["id"] == fav_id:
                assert fav["category_id"] is None

    def test_delete_other_user_category_fails(self, client, db, editor_user, editor_headers, viewer_user, viewer_headers):
        resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "我的分类"})
        cat_id = resp.json()["id"]

        resp = client.delete(f"/api/favorites/categories/{cat_id}", headers=viewer_headers)
        assert resp.status_code == 404

    def test_categories_are_per_user(self, client, db, editor_user, editor_headers, viewer_user, viewer_headers):
        client.post("/api/favorites/categories", headers=editor_headers, json={"name": "共同名称"})
        client.post("/api/favorites/categories", headers=viewer_headers, json={"name": "共同名称"})

        resp1 = client.get("/api/favorites/categories", headers=editor_headers)
        resp2 = client.get("/api/favorites/categories", headers=viewer_headers)
        assert len(resp1.json()) == 1
        assert len(resp2.json()) == 1
        assert resp1.json()[0]["id"] != resp2.json()[0]["id"]


class TestFavorites:
    def test_add_favorite(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        assert resp.status_code == 201
        data = resp.json()
        assert data["document_id"] == doc.id
        assert data["category_id"] is None

    def test_add_favorite_with_category(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        cat_resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "重要"})
        cat_id = cat_resp.json()["id"]

        resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id, "category_id": cat_id})
        assert resp.status_code == 201
        assert resp.json()["category_id"] == cat_id

    def test_add_favorite_duplicate(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        assert resp.status_code == 400

    def test_add_favorite_nonexistent_doc(self, client, editor_user, editor_headers):
        resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": 99999})
        assert resp.status_code == 404

    def test_add_favorite_nonexistent_category(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id, "category_id": 99999})
        assert resp.status_code == 404

    def test_add_favorite_deleted_doc(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        doc.is_deleted = True
        db.commit()

        resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        assert resp.status_code == 404

    def test_remove_favorite(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        fav_resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        fav_id = fav_resp.json()["id"]

        resp = client.delete(f"/api/favorites/{fav_id}", headers=editor_headers)
        assert resp.status_code == 204

    def test_remove_nonexistent_favorite(self, client, editor_user, editor_headers):
        resp = client.delete("/api/favorites/99999", headers=editor_headers)
        assert resp.status_code == 404

    def test_remove_other_user_favorite(self, client, db, editor_user, editor_headers, viewer_user, viewer_headers):
        doc = _create_doc_directly(db, editor_user.id)
        fav_resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        fav_id = fav_resp.json()["id"]

        resp = client.delete(f"/api/favorites/{fav_id}", headers=viewer_headers)
        assert resp.status_code == 404

    def test_list_all_favorites(self, client, db, editor_user, editor_headers):
        doc1 = _create_doc_directly(db, editor_user.id, "Doc 1")
        doc2 = _create_doc_directly(db, editor_user.id, "Doc 2")
        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc1.id})
        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc2.id})

        resp = client.get("/api/favorites", headers=editor_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_favorites_by_category(self, client, db, editor_user, editor_headers):
        doc1 = _create_doc_directly(db, editor_user.id, "Cat Doc 1")
        doc2 = _create_doc_directly(db, editor_user.id, "Cat Doc 2")
        cat_resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "筛选分类"})
        cat_id = cat_resp.json()["id"]

        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc1.id, "category_id": cat_id})
        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc2.id})

        resp = client.get("/api/favorites", headers=editor_headers, params={"category_id": cat_id})
        assert len(resp.json()) == 1
        assert resp.json()[0]["document_id"] == doc1.id

    def test_list_uncategorized_favorites(self, client, db, editor_user, editor_headers):
        doc1 = _create_doc_directly(db, editor_user.id, "Uncat Doc")
        doc2 = _create_doc_directly(db, editor_user.id, "Cat Doc")
        cat_resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "有分类"})
        cat_id = cat_resp.json()["id"]

        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc1.id})
        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc2.id, "category_id": cat_id})

        resp = client.get("/api/favorites", headers=editor_headers, params={"category_id": 0})
        assert len(resp.json()) == 1
        assert resp.json()[0]["document_id"] == doc1.id

    def test_move_favorite_to_category(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        fav_resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        fav_id = fav_resp.json()["id"]

        cat_resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "目标分类"})
        cat_id = cat_resp.json()["id"]

        resp = client.put(f"/api/favorites/{fav_id}/category", headers=editor_headers, json={"category_id": cat_id})
        assert resp.status_code == 200
        assert resp.json()["category_id"] == cat_id

    def test_move_favorite_to_uncategorized(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        cat_resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "源分类"})
        cat_id = cat_resp.json()["id"]

        fav_resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id, "category_id": cat_id})
        fav_id = fav_resp.json()["id"]

        resp = client.put(f"/api/favorites/{fav_id}/category", headers=editor_headers, json={"category_id": None})
        assert resp.status_code == 200
        assert resp.json()["category_id"] is None

    def test_move_favorite_invalid_category(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        fav_resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        fav_id = fav_resp.json()["id"]

        resp = client.put(f"/api/favorites/{fav_id}/category", headers=editor_headers, json={"category_id": 99999})
        assert resp.status_code == 404

    def test_favorite_status_favorited(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        fav_resp = client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})
        fav_id = fav_resp.json()["id"]

        resp = client.get(f"/api/favorites/status/{doc.id}", headers=editor_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_favorited"] is True
        assert data["favorite_id"] == fav_id

    def test_favorite_status_not_favorited(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id)
        resp = client.get(f"/api/favorites/status/{doc.id}", headers=editor_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_favorited"] is False
        assert data["favorite_id"] is None

    def test_category_count_updates(self, client, db, editor_user, editor_headers):
        doc1 = _create_doc_directly(db, editor_user.id, "Count Doc 1")
        doc2 = _create_doc_directly(db, editor_user.id, "Count Doc 2")
        cat_resp = client.post("/api/favorites/categories", headers=editor_headers, json={"name": "计数分类"})
        cat_id = cat_resp.json()["id"]

        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc1.id, "category_id": cat_id})
        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc2.id, "category_id": cat_id})

        resp = client.get("/api/favorites/categories", headers=editor_headers)
        for cat in resp.json():
            if cat["id"] == cat_id:
                assert cat["count"] == 2

    def test_favorites_require_auth(self, client):
        assert client.get("/api/favorites").status_code == 401
        assert client.post("/api/favorites", json={"document_id": 1}).status_code == 401
        assert client.get("/api/favorites/categories").status_code == 401


class TestQuickAccess:
    def test_quick_access_recent(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id, "Recent Doc")
        access = DocumentAccess(user_id=editor_user.id, document_id=doc.id)
        db.add(access)
        db.commit()

        resp = client.get("/api/favorites/quick-access", headers=editor_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "recent" in data
        assert "favorites" in data
        assert len(data["recent"]) == 1
        assert data["recent"][0]["title"] == "Recent Doc"

    def test_quick_access_favorites(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id, "Fav Doc")
        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})

        resp = client.get("/api/favorites/quick-access", headers=editor_headers)
        data = resp.json()
        assert len(data["favorites"]) == 1
        assert data["favorites"][0]["title"] == "Fav Doc"

    def test_quick_access_excludes_deleted(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id, "Deleted Fav")
        client.post("/api/favorites", headers=editor_headers, json={"document_id": doc.id})

        doc.is_deleted = True
        db.commit()

        resp = client.get("/api/favorites/quick-access", headers=editor_headers)
        data = resp.json()
        assert len(data["favorites"]) == 0

    def test_quick_access_limits_results(self, client, db, editor_user, editor_headers):
        for i in range(15):
            doc = _create_doc_directly(db, editor_user.id, f"Bulk Doc {i}")
            access = DocumentAccess(user_id=editor_user.id, document_id=doc.id)
            db.add(access)
        db.commit()

        resp = client.get("/api/favorites/quick-access", headers=editor_headers)
        data = resp.json()
        assert len(data["recent"]) <= 10

    def test_quick_access_requires_auth(self, client):
        resp = client.get("/api/favorites/quick-access")
        assert resp.status_code == 401


class TestDocumentAccessRecord:
    def test_record_access_on_view(self, client, db, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("a.txt", b"access test", "text/plain")},
            data={"title": "Access Test"},
        )
        doc_id = resp.json()["id"]

        client.get(f"/api/documents/{doc_id}", headers=editor_headers)

        access = db.query(DocumentAccess).filter(
            DocumentAccess.user_id == editor_user.id,
            DocumentAccess.document_id == doc_id,
        ).first()
        assert access is not None

    def test_record_access_explicit_endpoint(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id, "Explicit Access")

        resp = client.post(f"/api/documents/{doc.id}/access", headers=editor_headers)
        assert resp.status_code == 204

        access = db.query(DocumentAccess).filter(
            DocumentAccess.user_id == editor_user.id,
            DocumentAccess.document_id == doc.id,
        ).first()
        assert access is not None

    def test_record_access_updates_timestamp(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id, "Timestamp Doc")

        client.post(f"/api/documents/{doc.id}/access", headers=editor_headers)
        access1 = db.query(DocumentAccess).filter(
            DocumentAccess.user_id == editor_user.id,
            DocumentAccess.document_id == doc.id,
        ).first()
        time1 = access1.accessed_at

        client.post(f"/api/documents/{doc.id}/access", headers=editor_headers)
        db.refresh(access1)
        assert access1.accessed_at >= time1

    def test_record_access_nonexistent_doc(self, client, editor_user, editor_headers):
        resp = client.post("/api/documents/99999/access", headers=editor_headers)
        assert resp.status_code == 404

    def test_record_access_deleted_doc(self, client, db, editor_user, editor_headers):
        doc = _create_doc_directly(db, editor_user.id, "Deleted Access")
        doc.is_deleted = True
        db.commit()

        resp = client.post(f"/api/documents/{doc.id}/access", headers=editor_headers)
        assert resp.status_code == 404

    def test_record_access_requires_auth(self, client, db, editor_user):
        doc = _create_doc_directly(db, editor_user.id)
        resp = client.post(f"/api/documents/{doc.id}/access")
        assert resp.status_code == 401
