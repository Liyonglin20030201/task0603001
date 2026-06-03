from tests.conftest import create_test_user, get_auth_headers


def test_create_project(client, editor_user, editor_headers):
    response = client.post(
        "/api/projects",
        headers=editor_headers,
        json={"name": "Project Alpha", "description": "First project"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Project Alpha"
    assert data["owner_id"] == editor_user.id
    assert len(data["members"]) == 1
    assert data["members"][0]["role"] == "lead"


def test_list_projects(client, editor_user, editor_headers):
    client.post("/api/projects", headers=editor_headers, json={"name": "P1"})
    client.post("/api/projects", headers=editor_headers, json={"name": "P2"})

    response = client.get("/api/projects", headers=editor_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_project_admin_only(client, editor_user, editor_headers, admin_user, admin_headers):
    resp = client.post("/api/projects", headers=editor_headers, json={"name": "ToDelete"})
    project_id = resp.json()["id"]

    del_resp = client.delete(f"/api/projects/{project_id}", headers=editor_headers)
    assert del_resp.status_code == 403

    del_resp = client.delete(f"/api/projects/{project_id}", headers=admin_headers)
    assert del_resp.status_code == 204


def test_add_and_remove_member(client, db, editor_user, editor_headers, viewer_user):
    resp = client.post("/api/projects", headers=editor_headers, json={"name": "Team Project"})
    project_id = resp.json()["id"]

    add_resp = client.post(
        f"/api/projects/{project_id}/members",
        headers=editor_headers,
        json={"user_id": viewer_user.id, "role": "member"},
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["user_id"] == viewer_user.id

    members_resp = client.get(f"/api/projects/{project_id}/members", headers=editor_headers)
    assert len(members_resp.json()) == 2

    rm_resp = client.delete(f"/api/projects/{project_id}/members/{viewer_user.id}", headers=editor_headers)
    assert rm_resp.status_code == 204

    members_resp = client.get(f"/api/projects/{project_id}/members", headers=editor_headers)
    assert len(members_resp.json()) == 1


def test_duplicate_member_rejected(client, editor_user, editor_headers, viewer_user):
    resp = client.post("/api/projects", headers=editor_headers, json={"name": "Dup Test"})
    project_id = resp.json()["id"]

    client.post(f"/api/projects/{project_id}/members", headers=editor_headers, json={"user_id": viewer_user.id, "role": "member"})
    dup_resp = client.post(f"/api/projects/{project_id}/members", headers=editor_headers, json={"user_id": viewer_user.id, "role": "member"})
    assert dup_resp.status_code == 409
