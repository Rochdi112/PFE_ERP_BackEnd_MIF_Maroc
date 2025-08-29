#!/usr/bin/env python3
# Try to import the FastAPI app and print OpenAPI JSON; fallback to AST-based approximation if import fails

from __future__ import annotations
import json
import sys
from pathlib import Path
import os
import io
from contextlib import redirect_stdout, redirect_stderr

ROOT = Path(__file__).resolve().parents[1]


def try_runtime_openapi():
    try:
        sys.path.insert(0, str(ROOT))
        # Minimize side effects and noisy logs during import
        os.environ.setdefault("ENV", "test")
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        os.environ.setdefault("SQLALCHEMY_DATABASE_URL", "sqlite:///:memory:")
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            from app.main import app  # type: ignore
            spec = app.openapi()
        print(json.dumps(spec, ensure_ascii=False))
        return True
    except Exception as e:
        return False


def ast_fallback():
    import subprocess, json as _json
    script = ROOT / "scripts" / "ast_extract.py"
    data = _json.loads(subprocess.check_output([sys.executable, str(script)], cwd=str(ROOT)).decode("utf-8"))
    # Very small OpenAPI approximation
    paths = {}
    for ep in data.get("endpoints", []):
        path_item = paths.setdefault(ep["path"], {})
        path_item.setdefault(ep["method"].lower(), {
            "responses": {
                "200": {"description": "OK"}
            }
        })
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "ERP API (approx)", "version": "ast"},
        "paths": paths,
        "servers": [{"url": "/api/v1"}] if "/api/v1" in data.get("base_paths", []) else []
    }
    print(json.dumps(doc, ensure_ascii=False))


def main():
    if try_runtime_openapi():
        return 0
    ast_fallback()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
