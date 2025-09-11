from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.document_service import save_uploaded_file


def test_save_uploaded_file_no_extension_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIRECTORY", str(tmp_path))

    class BytesReader:
        def __init__(self, b: bytes):
            self._b = b

        def read(self):
            return self._b

    fake = SimpleNamespace(filename="nofile", file=BytesReader(b"x"))
    with pytest.raises(Exception):
        save_uploaded_file(fake)
