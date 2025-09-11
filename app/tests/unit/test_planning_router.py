from datetime import datetime
from unittest.mock import patch

from app.api.v1 import planning as planning_router


def test_create_new_planning_calls_service(monkeypatch):
    dummy = {"id": 1, "equipement_id": 2}
    with patch("app.api.v1.planning.create_planning", return_value=dummy) as cp:
        res = planning_router.create_new_planning(data={"titre": "t"}, db=None)
        assert res == dummy
        cp.assert_called_once()


def test_list_all_plannings_calls_service(monkeypatch):
    dummy = [{"id": 1}, {"id": 2}]
    with patch("app.api.v1.planning.get_all_plannings", return_value=dummy) as gp:
        res = planning_router.list_all_plannings(db=None, user={"id": 1})
        assert res == dummy
        gp.assert_called_once()


def test_get_and_update_planning(monkeypatch):
    dummy = {"id": 42}
    with patch("app.api.v1.planning.get_planning_by_id", return_value=dummy):
        res = planning_router.get_planning(42, db=None, user={"id": 1})
        assert res == dummy

    with patch("app.api.v1.planning.update_planning_dates", return_value=dummy):
        res2 = planning_router.update_planning_next_date(42, datetime.utcnow(), db=None)
        assert res2 == dummy

    with patch(
        "app.services.planning_service.update_planning_frequence", return_value=dummy
    ):
        res3 = planning_router.update_planning(
            42, payload={"frequence": "mensuel"}, db=None
        )
        assert res3 == dummy

    with patch("app.services.planning_service.delete_planning") as dp:
        # delete returns None and endpoint returns None
        res4 = planning_router.delete_planning_endpoint(42, db=None)
        assert res4 is None
        dp.assert_called_once()
