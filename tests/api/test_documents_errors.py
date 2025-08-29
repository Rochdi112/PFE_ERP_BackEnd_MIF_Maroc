import io
import pytest


def test_upload_to_missing_intervention(client, admin_token):
    data = {
        "intervention_id": 9999,
    }
    # httpx expects files mapping as (filename, fileobj) or (filename, fileobj, content_type)
    file = ("file.txt", b"hello", "text/plain")
    r = client.post("/documents/upload", data=data, files={"file": file}, headers={"Authorization": f"Bearer {admin_token}"})
    # depending on validation vs service logic, server may return 422 or 404
    assert r.status_code in (404, 422)


def test_delete_nonexistent_document(client, admin_token):
    r = client.delete("/documents/99999", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 404
