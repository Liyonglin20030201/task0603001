import pytest
from datetime import datetime, timedelta, timezone

from app.models.document import Document
from app.models.share_link import ShareLink
from app.services.auth_service import hash_password


class TestCreateShareLink:
    def test_create_permanent_link(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Share Doc", original_filename="s.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"is_permanent": True},
            headers=editor_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["document_id"] == doc.id
        assert data["is_permanent"] is True
        assert data["token"]
        assert data["has_password"] is False
        assert data["is_active"] is True

    def test_create_temporary_link_with_expiration(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Temp Doc", original_filename="t.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        resp = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"is_permanent": False, "expires_at": expires, "max_access_count": 5},
            headers=editor_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["is_permanent"] is False
        assert data["max_access_count"] == 5

    def test_temporary_link_requires_expiration(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="No Exp Doc", original_filename="n.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"is_permanent": False},
            headers=editor_headers,
        )
        assert resp.status_code == 422

    def test_create_with_password(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Pwd Doc", original_filename="p.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"is_permanent": True, "password": "secret123"},
            headers=editor_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["has_password"] is True

    def test_viewer_cannot_create(self, client, viewer_headers, editor_user, db):
        doc = Document(
            title="V Doc", original_filename="v.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.post(
            f"/api/documents/{doc.id}/shares",
            json={"is_permanent": True},
            headers=viewer_headers,
        )
        assert resp.status_code == 403


class TestAccessSharedDocument:
    def test_public_access_no_auth(self, client, editor_user, db):
        doc = Document(
            title="Public Doc", original_filename="pub.txt", file_type="txt",
            owner_id=editor_user.id, content="shared content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="test-public-token", created_by=editor_user.id,
            is_permanent=True, is_active=True,
        )
        db.add(share)
        db.commit()

        resp = client.get("/api/shared/test-public-token")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Public Doc"
        assert data["content"] == "shared content"

    def test_expired_link(self, client, editor_user, db):
        doc = Document(
            title="Exp Doc", original_filename="e.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="expired-token", created_by=editor_user.id,
            is_permanent=False, is_active=True,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(share)
        db.commit()

        resp = client.get("/api/shared/expired-token")
        assert resp.status_code == 410

    def test_exhausted_link(self, client, editor_user, db):
        doc = Document(
            title="Max Doc", original_filename="m.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="maxed-token", created_by=editor_user.id,
            is_permanent=True, is_active=True,
            max_access_count=1, current_access_count=1,
        )
        db.add(share)
        db.commit()

        resp = client.get("/api/shared/maxed-token")
        assert resp.status_code == 410

    def test_password_protected_requires_password(self, client, editor_user, db):
        doc = Document(
            title="Pwd Doc", original_filename="pw.txt", file_type="txt",
            owner_id=editor_user.id, content="protected content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="pwd-token", created_by=editor_user.id,
            is_permanent=True, is_active=True,
            password_hash=hash_password("mypass"),
        )
        db.add(share)
        db.commit()

        resp = client.get("/api/shared/pwd-token")
        assert resp.status_code == 403
        assert "Password required" in resp.json()["detail"]

    def test_password_protected_correct_password(self, client, editor_user, db):
        doc = Document(
            title="Pwd OK Doc", original_filename="pok.txt", file_type="txt",
            owner_id=editor_user.id, content="secret content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="pwd-ok-token", created_by=editor_user.id,
            is_permanent=True, is_active=True,
            password_hash=hash_password("correct"),
        )
        db.add(share)
        db.commit()

        resp = client.post("/api/shared/pwd-ok-token/verify", json={"password": "correct"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Pwd OK Doc"

    def test_password_protected_wrong_password(self, client, editor_user, db):
        doc = Document(
            title="Pwd Fail Doc", original_filename="pf.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="pwd-fail-token", created_by=editor_user.id,
            is_permanent=True, is_active=True,
            password_hash=hash_password("right"),
        )
        db.add(share)
        db.commit()

        resp = client.post("/api/shared/pwd-fail-token/verify", json={"password": "wrong"})
        assert resp.status_code == 403
        assert "Invalid password" in resp.json()["detail"]

    def test_deactivated_link(self, client, editor_user, db):
        doc = Document(
            title="Deact Doc", original_filename="d.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="deact-token", created_by=editor_user.id,
            is_permanent=True, is_active=False,
        )
        db.add(share)
        db.commit()

        resp = client.get("/api/shared/deact-token")
        assert resp.status_code == 410

    def test_access_count_increments(self, client, editor_user, db):
        doc = Document(
            title="Count Doc", original_filename="c.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="count-token", created_by=editor_user.id,
            is_permanent=True, is_active=True,
        )
        db.add(share)
        db.commit()

        client.get("/api/shared/count-token")
        client.get("/api/shared/count-token")

        db.refresh(share)
        assert share.current_access_count == 2

    def test_not_found_token(self, client):
        resp = client.get("/api/shared/nonexistent-token")
        assert resp.status_code == 404


class TestListAndDeactivateShares:
    def test_list_shares(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="List Doc", original_filename="l.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        for i in range(3):
            db.add(ShareLink(
                document_id=doc.id, token=f"list-token-{i}", created_by=editor_user.id,
                is_permanent=True, is_active=True,
            ))
        db.commit()

        resp = client.get(f"/api/documents/{doc.id}/shares", headers=editor_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_deactivate_share(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Deact Doc", original_filename="da.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        share = ShareLink(
            document_id=doc.id, token="to-deact", created_by=editor_user.id,
            is_permanent=True, is_active=True,
        )
        db.add(share)
        db.commit()
        db.refresh(share)

        resp = client.delete(f"/api/documents/{doc.id}/shares/{share.id}", headers=editor_headers)
        assert resp.status_code == 204

        db.refresh(share)
        assert share.is_active is False
