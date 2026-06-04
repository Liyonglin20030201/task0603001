import pytest
from datetime import datetime, timezone

from app.models.document import Document
from app.models.project import Project
from app.models.subscription import Subscription
from app.models.notification import Notification
from app.models.comment import Comment


class TestSubscriptions:
    def test_subscribe_to_document(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Sub Doc", original_filename="s.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.post(
            "/api/subscriptions",
            json={"document_id": doc.id},
            headers=editor_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["document_id"] == doc.id
        assert data["user_id"] == editor_user.id

    def test_subscribe_to_project(self, client, editor_headers, editor_user, db):
        project = Project(
            name="Sub Project", description="test", created_by=editor_user.id, owner_id=editor_user.id,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        resp = client.post(
            "/api/subscriptions",
            json={"project_id": project.id},
            headers=editor_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["project_id"] == project.id

    def test_subscribe_requires_target(self, client, editor_headers):
        resp = client.post("/api/subscriptions", json={}, headers=editor_headers)
        assert resp.status_code == 422

    def test_subscribe_only_one_target(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Both Doc", original_filename="b.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        project = Project(
            name="Both Project", description="test", created_by=editor_user.id, owner_id=editor_user.id,
        )
        db.add_all([doc, project])
        db.commit()
        db.refresh(doc)
        db.refresh(project)

        resp = client.post(
            "/api/subscriptions",
            json={"document_id": doc.id, "project_id": project.id},
            headers=editor_headers,
        )
        assert resp.status_code == 422

    def test_duplicate_subscription_rejected(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Dup Doc", original_filename="dup.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        client.post("/api/subscriptions", json={"document_id": doc.id}, headers=editor_headers)
        resp = client.post("/api/subscriptions", json={"document_id": doc.id}, headers=editor_headers)
        assert resp.status_code == 400

    def test_list_subscriptions(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="List Sub Doc", original_filename="ls.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        sub = Subscription(user_id=editor_user.id, document_id=doc.id)
        db.add(sub)
        db.commit()

        resp = client.get("/api/subscriptions", headers=editor_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_unsubscribe(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Unsub Doc", original_filename="u.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        sub = Subscription(user_id=editor_user.id, document_id=doc.id)
        db.add(sub)
        db.commit()
        db.refresh(sub)

        resp = client.delete(f"/api/subscriptions/{sub.id}", headers=editor_headers)
        assert resp.status_code == 204

        resp = client.get("/api/subscriptions", headers=editor_headers)
        assert len(resp.json()) == 0


class TestNotifications:
    def test_notification_on_new_comment(self, client, editor_headers, admin_headers, editor_user, admin_user, db):
        doc = Document(
            title="Notify Doc", original_filename="n.txt", file_type="txt",
            owner_id=admin_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        sub = Subscription(user_id=editor_user.id, document_id=doc.id)
        db.add(sub)
        db.commit()

        client.post(
            f"/api/documents/{doc.id}/comments",
            json={"content": "Hello"},
            headers=admin_headers,
        )

        resp = client.get("/api/notifications", headers=editor_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["unread_count"] == 1
        assert data["items"][0]["event_type"] == "new_comment"
        assert doc.title in data["items"][0]["message"]

    def test_no_self_notification(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Self Doc", original_filename="self.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        sub = Subscription(user_id=editor_user.id, document_id=doc.id)
        db.add(sub)
        db.commit()

        client.post(
            f"/api/documents/{doc.id}/comments",
            json={"content": "My own comment"},
            headers=editor_headers,
        )

        resp = client.get("/api/notifications", headers=editor_headers)
        assert resp.json()["total"] == 0

    def test_project_subscription_catches_doc_events(self, client, editor_headers, admin_headers, editor_user, admin_user, db):
        project = Project(
            name="Notif Project", description="test", created_by=admin_user.id, owner_id=admin_user.id,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        doc = Document(
            title="Project Doc", original_filename="pd.txt", file_type="txt",
            owner_id=admin_user.id, content="content", project_id=project.id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        sub = Subscription(user_id=editor_user.id, project_id=project.id)
        db.add(sub)
        db.commit()

        client.post(
            f"/api/documents/{doc.id}/comments",
            json={"content": "Project comment"},
            headers=admin_headers,
        )

        resp = client.get("/api/notifications", headers=editor_headers)
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["event_type"] == "new_comment"

    def test_mark_notification_read(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Read Doc", original_filename="r.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        notif = Notification(
            user_id=editor_user.id, event_type="new_version",
            document_id=doc.id, message="Test notification",
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        resp = client.put(f"/api/notifications/{notif.id}/read", headers=editor_headers)
        assert resp.status_code == 204

        resp = client.get("/api/notifications", headers=editor_headers)
        assert resp.json()["unread_count"] == 0
        assert resp.json()["items"][0]["is_read"] is True

    def test_mark_all_read(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="All Read Doc", original_filename="ar.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        for i in range(3):
            db.add(Notification(
                user_id=editor_user.id, event_type="new_comment",
                document_id=doc.id, message=f"Notification {i}",
            ))
        db.commit()

        resp = client.put("/api/notifications/read-all", headers=editor_headers)
        assert resp.status_code == 204

        resp = client.get("/api/notifications", headers=editor_headers)
        assert resp.json()["unread_count"] == 0
        assert resp.json()["total"] == 3

    def test_notification_list_pagination(self, client, editor_headers, editor_user, db):
        doc = Document(
            title="Pag Doc", original_filename="pag.txt", file_type="txt",
            owner_id=editor_user.id, content="content",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        for i in range(5):
            db.add(Notification(
                user_id=editor_user.id, event_type="new_version",
                document_id=doc.id, message=f"Notification {i}",
            ))
        db.commit()

        resp = client.get("/api/notifications?page=1&page_size=2", headers=editor_headers)
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
