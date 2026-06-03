import pytest

from app.services.diff_service import compute_diff
from tests.conftest import create_test_user, get_auth_headers
from app.models.document import Document
from app.models.document_version import DocumentVersion
import os


class TestDiffService:
    def test_identical_texts(self):
        text = "line1\nline2\nline3"
        diff = compute_diff(text, text)
        assert all(d["type"] == "equal" for d in diff)
        assert len(diff) == 3

    def test_addition(self):
        left = "line1\nline2"
        right = "line1\nline2\nline3"
        diff = compute_diff(left, right)

        types = [d["type"] for d in diff]
        assert "add" in types
        added = [d for d in diff if d["type"] == "add"]
        assert len(added) == 1
        assert added[0]["content_right"] == "line3"

    def test_deletion(self):
        left = "line1\nline2\nline3"
        right = "line1\nline3"
        diff = compute_diff(left, right)

        types = [d["type"] for d in diff]
        assert "delete" in types
        deleted = [d for d in diff if d["type"] == "delete"]
        assert len(deleted) == 1
        assert deleted[0]["content_left"] == "line2"

    def test_change(self):
        left = "line1\nold content\nline3"
        right = "line1\nnew content\nline3"
        diff = compute_diff(left, right)

        types = [d["type"] for d in diff]
        assert "change" in types
        changes = [d for d in diff if d["type"] == "change"]
        assert len(changes) == 1
        assert changes[0]["content_left"] == "old content"
        assert changes[0]["content_right"] == "new content"

    def test_empty_left(self):
        diff = compute_diff("", "line1\nline2")
        assert len(diff) == 2
        assert all(d["type"] == "add" for d in diff)

    def test_empty_right(self):
        diff = compute_diff("line1\nline2", "")
        assert len(diff) == 2
        assert all(d["type"] == "delete" for d in diff)

    def test_both_empty(self):
        diff = compute_diff("", "")
        assert diff == []

    def test_line_numbers_equal(self):
        left = "a\nb\nc"
        right = "a\nb\nc"
        diff = compute_diff(left, right)
        assert diff[0]["line_left"] == 1
        assert diff[0]["line_right"] == 1
        assert diff[2]["line_left"] == 3
        assert diff[2]["line_right"] == 3

    def test_line_numbers_with_addition(self):
        left = "a\nc"
        right = "a\nb\nc"
        diff = compute_diff(left, right)
        added = [d for d in diff if d["type"] == "add"]
        assert added[0]["line_left"] is None
        assert added[0]["line_right"] is not None

    def test_line_numbers_with_deletion(self):
        left = "a\nb\nc"
        right = "a\nc"
        diff = compute_diff(left, right)
        deleted = [d for d in diff if d["type"] == "delete"]
        assert deleted[0]["line_left"] is not None
        assert deleted[0]["line_right"] is None

    def test_multiple_changes(self):
        left = "a\nb\nc\nd\ne"
        right = "a\nB\nc\nD\ne"
        diff = compute_diff(left, right)
        changes = [d for d in diff if d["type"] == "change"]
        assert len(changes) == 2
        assert changes[0]["content_left"] == "b"
        assert changes[0]["content_right"] == "B"
        assert changes[1]["content_left"] == "d"
        assert changes[1]["content_right"] == "D"

    def test_replace_different_lengths(self):
        left = "a\nb\nc"
        right = "a\nx\ny\nz\nc"
        diff = compute_diff(left, right)
        non_equal = [d for d in diff if d["type"] != "equal"]
        assert len(non_equal) > 0

    def test_large_diff(self):
        left = "\n".join([f"line {i}" for i in range(100)])
        right = "\n".join([f"line {i}" for i in range(50)] + ["NEW"] + [f"line {i}" for i in range(50, 100)])
        diff = compute_diff(left, right)
        assert len(diff) > 100
        added = [d for d in diff if d["type"] == "add"]
        assert any(d["content_right"] == "NEW" for d in added)

    def test_unicode_content(self):
        left = "第一行\n第二行\n第三行"
        right = "第一行\n修改行\n第三行"
        diff = compute_diff(left, right)
        changes = [d for d in diff if d["type"] == "change"]
        assert len(changes) == 1
        assert changes[0]["content_left"] == "第二行"
        assert changes[0]["content_right"] == "修改行"

    def test_whitespace_differences(self):
        left = "hello world\n  indented"
        right = "hello world\n    indented"
        diff = compute_diff(left, right)
        changes = [d for d in diff if d["type"] == "change"]
        assert len(changes) == 1


class TestVersionCompareAPI:
    def _upload_doc(self, client, headers, tmp_path, monkeypatch, content=b"v1 content"):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))
        resp = client.post(
            "/api/documents", headers=headers,
            files={"file": ("doc.txt", content, "text/plain")},
            data={"title": "Diff Test Doc"},
        )
        return resp.json()["id"]

    def test_compare_two_versions(self, client, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("doc.txt", b"version one content", "text/plain")},
            data={"title": "Compare Doc"},
        )
        doc_id = resp.json()["id"]

        client.post(
            f"/api/documents/{doc_id}/versions", headers=editor_headers,
            files={"file": ("doc.txt", b"version two content modified", "text/plain")},
        )

        resp = client.get(
            f"/api/documents/{doc_id}/versions/compare",
            headers=editor_headers,
            params={"v1": 1, "v2": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == doc_id
        assert data["version_left"] == 1
        assert data["version_right"] == 2
        assert "diff_lines" in data
        assert "stats" in data
        assert "additions" in data["stats"]
        assert "deletions" in data["stats"]
        assert "changes" in data["stats"]
        assert "total_lines" in data["stats"]

    def test_compare_same_version(self, client, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("doc.txt", b"same content", "text/plain")},
            data={"title": "Same Version"},
        )
        doc_id = resp.json()["id"]

        resp = client.get(
            f"/api/documents/{doc_id}/versions/compare",
            headers=editor_headers,
            params={"v1": 1, "v2": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["additions"] == 0
        assert data["stats"]["deletions"] == 0
        assert data["stats"]["changes"] == 0

    def test_compare_nonexistent_version(self, client, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("doc.txt", b"content", "text/plain")},
            data={"title": "No V2"},
        )
        doc_id = resp.json()["id"]

        resp = client.get(
            f"/api/documents/{doc_id}/versions/compare",
            headers=editor_headers,
            params={"v1": 1, "v2": 99},
        )
        assert resp.status_code == 404

    def test_compare_nonexistent_document(self, client, editor_user, editor_headers):
        resp = client.get(
            "/api/documents/99999/versions/compare",
            headers=editor_headers,
            params={"v1": 1, "v2": 2},
        )
        assert resp.status_code == 404

    def test_compare_requires_auth(self, client, db, editor_user):
        doc = Document(
            title="Auth Test", original_filename="a.txt", file_type="txt",
            content="c", owner_id=editor_user.id, current_version=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        resp = client.get(
            f"/api/documents/{doc.id}/versions/compare",
            params={"v1": 1, "v2": 2},
        )
        assert resp.status_code == 401

    def test_compare_respects_permission(self, client, db, editor_user, editor_headers, viewer_user, viewer_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("doc.txt", b"private", "text/plain")},
            data={"title": "Private Doc"},
        )
        doc_id = resp.json()["id"]

        from app.models.document_permission import DocumentPermission
        perm = DocumentPermission(
            document_id=doc_id, user_id=editor_user.id,
            permission_level="admin", granted_by=editor_user.id,
        )
        db.add(perm)
        db.commit()

        resp = client.get(
            f"/api/documents/{doc_id}/versions/compare",
            headers=viewer_headers,
            params={"v1": 1, "v2": 1},
        )
        assert resp.status_code == 403

    def test_compare_stats_accuracy(self, client, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        v1_content = "line1\nline2\nline3\nline4\nline5"
        v2_content = "line1\nmodified\nline3\nline5\nnew_line"

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("doc.txt", v1_content.encode(), "text/plain")},
            data={"title": "Stats Doc"},
        )
        doc_id = resp.json()["id"]

        client.post(
            f"/api/documents/{doc_id}/versions", headers=editor_headers,
            files={"file": ("doc.txt", v2_content.encode(), "text/plain")},
        )

        resp = client.get(
            f"/api/documents/{doc_id}/versions/compare",
            headers=editor_headers,
            params={"v1": 1, "v2": 2},
        )
        data = resp.json()
        stats = data["stats"]
        assert stats["total_lines"] == len(data["diff_lines"])
        assert stats["additions"] >= 0
        assert stats["deletions"] >= 0
        assert stats["changes"] >= 0

    def test_compare_diff_line_structure(self, client, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("doc.txt", b"aaa\nbbb", "text/plain")},
            data={"title": "Structure Doc"},
        )
        doc_id = resp.json()["id"]

        client.post(
            f"/api/documents/{doc_id}/versions", headers=editor_headers,
            files={"file": ("doc.txt", b"aaa\nccc", "text/plain")},
        )

        resp = client.get(
            f"/api/documents/{doc_id}/versions/compare",
            headers=editor_headers,
            params={"v1": 1, "v2": 2},
        )
        data = resp.json()
        for line in data["diff_lines"]:
            assert "type" in line
            assert line["type"] in ("equal", "add", "delete", "change")
            assert "line_left" in line
            assert "line_right" in line
            assert "content_left" in line
            assert "content_right" in line

    def test_compare_multiline_txt(self, client, editor_user, editor_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.UPLOAD_DIR", str(tmp_path / "uploads"))
        monkeypatch.setattr("app.config.settings.PREVIEW_DIR", str(tmp_path / "previews"))

        v1 = "\n".join([f"paragraph {i} with some text" for i in range(20)])
        v2_lines = [f"paragraph {i} with some text" for i in range(20)]
        v2_lines[5] = "modified paragraph 5"
        v2_lines[10] = "modified paragraph 10"
        v2_lines.insert(15, "inserted new line")
        v2 = "\n".join(v2_lines)

        resp = client.post(
            "/api/documents", headers=editor_headers,
            files={"file": ("big.txt", v1.encode(), "text/plain")},
            data={"title": "Multiline Doc"},
        )
        doc_id = resp.json()["id"]

        client.post(
            f"/api/documents/{doc_id}/versions", headers=editor_headers,
            files={"file": ("big.txt", v2.encode(), "text/plain")},
        )

        resp = client.get(
            f"/api/documents/{doc_id}/versions/compare",
            headers=editor_headers,
            params={"v1": 1, "v2": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["changes"] >= 2
        assert data["stats"]["additions"] >= 1
