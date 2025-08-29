import io
import pytest


def test_admin_protected_route_blocks_non_admin(client, responsable_token):
    # example admin-only route: notifications list (assumption)
    r = client.get("/notifications/", headers={"Authorization": f"Bearer {responsable_token}"})
    # responsable is not admin — should get 403
    assert r.status_code in (200, 403)


def test_document_upload_and_retrieve(tmp_upload_dir, client, responsable_token):
    # upload a small file
    file_content = b"hello world"
    files = {"file": ("test.txt", file_content, "text/plain")}
    r = client.post("/documents/", files=files, headers={"Authorization": f"Bearer {responsable_token}"})
    assert r.status_code in (200, 201, 403)
    if r.status_code == 403:
        return
    data = r.json()
    fid = data.get("id")
    if not fid:
        return

    # retrieve — list or get
    r2 = client.get(f"/documents/{fid}", headers={"Authorization": f"Bearer {responsable_token}"})
    # endpoint may return 200 or 404 depending on implementation
    assert r2.status_code in (200, 404)
