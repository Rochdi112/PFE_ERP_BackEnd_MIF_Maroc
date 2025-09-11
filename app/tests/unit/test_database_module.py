import sys

from app.db import database


def test_engine_is_sqlite_in_pytest_mode(monkeypatch):
    # Simulate pytest module present
    monkeypatch.setitem(sys.modules, "pytest", object())
    eng = database._create_default_engine()
    assert eng is not None
    assert eng.url.get_backend_name() == "sqlite"


def test_sessionlocal_and_schema_init(monkeypatch, tmp_path):
    # Ensure engine is sqlite for safe schema create
    monkeypatch.setitem(sys.modules, "pytest", object())
    eng = database._create_default_engine()
    # set engine temporarily
    monkeypatch.setattr(database, "engine", eng)
    # ensure SessionLocal returns a session
    sess = database.SessionLocal()
    assert sess is not None
    sess.close()


def test_get_db_generator(monkeypatch):
    monkeypatch.setitem(sys.modules, "pytest", object())
    eng = database._create_default_engine()
    monkeypatch.setattr(database, "engine", eng)
    gen = database.get_db()
    db = next(gen)
    assert db is not None
    try:
        # allowed to do queries (no models required for this smoke test)
        pass
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
