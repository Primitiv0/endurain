from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from tests._helpers.db import setup_mock_execute
from tests._helpers.models import mock_model


class TestGetGearUserById:
    def test_success(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, user_id=1)
        setup_mock_execute(mock_db, return_one_or_none=g)
        r = crud.get_gear_user_by_id(user_id=1, gear_id=1, db=mock_db)
        assert r is g

    def test_not_found(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_one_or_none=None)
        r = crud.get_gear_user_by_id(user_id=1, gear_id=999, db=mock_db)
        assert r is None

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_user_by_id(user_id=1, gear_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetGearActivityStats:
    def test_success(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.return_value.one.return_value = (50000.0, 7200.0)
        r = crud.get_gear_activity_stats(gear_id=1, db=mock_db)
        assert r == {"total_distance": 50000.0, "total_time": 7200.0}

    def test_zero_values(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.return_value.one.return_value = (0.0, 0.0)
        r = crud.get_gear_activity_stats(gear_id=1, db=mock_db)
        assert r == {"total_distance": 0.0, "total_time": 0.0}

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_activity_stats(gear_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetGearComponentsTotalCost:
    def test_success(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.return_value.scalar_one.return_value = 1500.0
        r = crud.get_gear_components_total_cost(gear_id=1, user_id=1, db=mock_db)
        assert r == 1500.0

    def test_zero(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.return_value.scalar_one.return_value = 0.0
        r = crud.get_gear_components_total_cost(gear_id=1, user_id=1, db=mock_db)
        assert r == 0.0

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_components_total_cost(gear_id=1, user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetGearsNumber:
    def test_success(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.return_value.scalar_one.return_value = 42
        r = crud.get_gears_number(db=mock_db)
        assert r == 42

    def test_zero(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.return_value.scalar_one.return_value = 0
        r = crud.get_gears_number(db=mock_db)
        assert r == 0

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gears_number(db=mock_db)
        assert e.value.status_code == 500


class TestGetGearUsersWithPagination:
    def test_success_defaults(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, user_id=1)
        setup_mock_execute(mock_db, return_scalars_all=[g])
        r = crud.get_gear_users_with_pagination(user_id=1, db=mock_db)
        assert r == [g]

    def test_success_paginated(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, user_id=1)
        setup_mock_execute(mock_db, return_scalars_all=[g])
        r = crud.get_gear_users_with_pagination(user_id=1, db=mock_db, page_number=1, num_records=10)
        assert r == [g]

    def test_success_hide_inactive(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, user_id=1, active=True)
        setup_mock_execute(mock_db, return_scalars_all=[g])
        r = crud.get_gear_users_with_pagination(user_id=1, db=mock_db, show_inactive=False)
        assert r == [g]

    def test_empty(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_scalars_all=[])
        r = crud.get_gear_users_with_pagination(user_id=1, db=mock_db)
        assert r == []

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_users_with_pagination(user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetGearUser:
    def test_success(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, user_id=1)
        setup_mock_execute(mock_db, return_scalars_all=[g])
        r = crud.get_gear_user(user_id=1, db=mock_db)
        assert r == [g]

    def test_empty(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_scalars_all=[])
        r = crud.get_gear_user(user_id=1, db=mock_db)
        assert r == []

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_user(user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetGearUserContainsNickname:
    def test_success(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, nickname="Mountain Bike")
        setup_mock_execute(mock_db, return_scalars_all=[g])
        r = crud.get_gear_user_contains_nickname(user_id=1, nickname="mountain", db=mock_db)
        assert r == [g]

    def test_empty(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_scalars_all=[])
        r = crud.get_gear_user_contains_nickname(user_id=1, nickname="nonexistent", db=mock_db)
        assert r == []

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_user_contains_nickname(user_id=1, nickname="test", db=mock_db)
        assert e.value.status_code == 500


class TestGetGearUserByNickname:
    def test_success(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, nickname="Road Bike")
        setup_mock_execute(mock_db, return_one_or_none=g)
        r = crud.get_gear_user_by_nickname(user_id=1, nickname="Road+Bike", db=mock_db)
        assert r is g

    def test_not_found(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_one_or_none=None)
        r = crud.get_gear_user_by_nickname(user_id=1, nickname="Unknown", db=mock_db)
        assert r is None

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_user_by_nickname(user_id=1, nickname="Test", db=mock_db)
        assert e.value.status_code == 500


class TestGetGearByTypeAndUser:
    def test_success(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, gear_type=1)
        setup_mock_execute(mock_db, return_scalars_all=[g])
        r = crud.get_gear_by_type_and_user(gear_type=1, user_id=1, db=mock_db)
        assert r == [g]

    def test_empty(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_scalars_all=[])
        r = crud.get_gear_by_type_and_user(gear_type=1, user_id=1, db=mock_db)
        assert r == []

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_by_type_and_user(gear_type=1, user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetGearByStravaIdFromUserId:
    def test_success(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, strava_gear_id="strava_123")
        setup_mock_execute(mock_db, return_one_or_none=g)
        r = crud.get_gear_by_strava_id_from_user_id(gear_strava_id="strava_123", user_id=1, db=mock_db)
        assert r is g

    def test_not_found(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_one_or_none=None)
        r = crud.get_gear_by_strava_id_from_user_id(gear_strava_id="strava_999", user_id=1, db=mock_db)
        assert r is None

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_by_strava_id_from_user_id(gear_strava_id="strava_123", user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetGearByGarminconnectIdFromUserId:
    def test_success(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        g = mock_model(m.Gear, id=1, garminconnect_gear_id="garmin_123")
        setup_mock_execute(mock_db, return_one_or_none=g)
        r = crud.get_gear_by_garminconnect_id_from_user_id(gear_garminconnect_id="garmin_123", user_id=1, db=mock_db)
        assert r is g

    def test_not_found(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_one_or_none=None)
        r = crud.get_gear_by_garminconnect_id_from_user_id(gear_garminconnect_id="garmin_999", user_id=1, db=mock_db)
        assert r is None

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_gear_by_garminconnect_id_from_user_id(gear_garminconnect_id="garmin_123", user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestCreateMultipleGears:
    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    @patch("gears.gear.crud.core_logger.print_to_log_and_console")
    def test_success_single(self, mock_log, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = None
        mock_transform.return_value = MagicMock()

        gear = s.GearCreate(nickname="Test", gear_type=1)
        crud.create_multiple_gears([gear], user_id=1, db=mock_db)
        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    @patch("gears.gear.crud.core_logger.print_to_log_and_console")
    def test_success_multiple(self, mock_log, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = None
        mock_transform.return_value = MagicMock()

        gears_list = [
            s.GearCreate(nickname="Bike", gear_type=1),
            s.GearCreate(nickname="Shoes", gear_type=2),
        ]
        crud.create_multiple_gears(gears_list, user_id=1, db=mock_db)
        assert mock_db.add_all.call_count == 1
        mock_db.commit.assert_called_once()

    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    @patch("gears.gear.crud.core_logger.print_to_log_and_console")
    def test_dedup_by_nickname(self, mock_log, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = None
        mock_transform.return_value = MagicMock()

        gears_list = [
            s.GearCreate(nickname="Bike", gear_type=1),
            s.GearCreate(nickname="bike", gear_type=1),
        ]
        crud.create_multiple_gears(gears_list, user_id=1, db=mock_db)
        mock_db.add_all.assert_called_once()
        assert mock_log.call_count == 1

    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    @patch("gears.gear.crud.core_logger.print_to_log_and_console")
    def test_skip_existing(self, mock_log, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = MagicMock()
        mock_transform.return_value = MagicMock()

        gear = s.GearCreate(nickname="Existing", gear_type=1)
        crud.create_multiple_gears([gear], user_id=1, db=mock_db)
        mock_db.add_all.assert_not_called()

    @patch("gears.gear.crud.core_logger.print_to_log_and_console")
    def test_empty_input(self, mock_log, mock_db):
        import gears.gear.crud as crud

        crud.create_multiple_gears([], user_id=1, db=mock_db)
        mock_db.add_all.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch("gears.gear.crud.core_logger.print_to_log_and_console")
    def test_all_invalid(self, mock_log, mock_db):
        import gears.gear.crud as crud

        crud.create_multiple_gears([None, None], user_id=1, db=mock_db)
        mock_db.add_all.assert_not_called()

    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    @patch("gears.gear.crud.core_logger.print_to_log_and_console")
    def test_integrity_error(self, mock_log, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = None
        mock_transform.return_value = MagicMock()
        mock_db.commit.side_effect = IntegrityError("stmt", "params", "orig")

        gear = s.GearCreate(nickname="Test", gear_type=1)
        with pytest.raises(HTTPException) as e:
            crud.create_multiple_gears([gear], user_id=1, db=mock_db)
        assert e.value.status_code == 409
        mock_db.rollback.assert_called_once()

    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    @patch("gears.gear.crud.core_logger.print_to_log_and_console")
    def test_db_error(self, mock_log, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = None
        mock_transform.return_value = MagicMock()
        mock_db.commit.side_effect = SQLAlchemyError("err")

        gear = s.GearCreate(nickname="Test", gear_type=1)
        with pytest.raises(HTTPException) as e:
            crud.create_multiple_gears([gear], user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestCreateGear:
    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    def test_success(self, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = None
        new_gear = MagicMock()
        new_gear.id = 1
        mock_transform.return_value = new_gear

        gear = s.GearCreate(nickname="New Gear", gear_type=1)
        r = crud.create_gear(gear=gear, user_id=1, db=mock_db)
        assert r is new_gear
        mock_db.add.assert_called_once_with(new_gear)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(new_gear)

    @patch("gears.gear.crud.get_gear_user_by_nickname")
    def test_already_exists(self, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = MagicMock()

        gear = s.GearCreate(nickname="Exists", gear_type=1)
        with pytest.raises(HTTPException) as e:
            crud.create_gear(gear=gear, user_id=1, db=mock_db)
        assert e.value.status_code == 409

    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    def test_integrity_error(self, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = None
        mock_transform.return_value = MagicMock()
        mock_db.commit.side_effect = IntegrityError("stmt", "params", "orig")

        gear = s.GearCreate(nickname="New Gear", gear_type=1)
        with pytest.raises(HTTPException) as e:
            crud.create_gear(gear=gear, user_id=1, db=mock_db)
        assert e.value.status_code == 409
        mock_db.rollback.assert_called_once()

    @patch("gears.gear.crud.get_gear_user_by_nickname")
    @patch("gears.gear.crud.gears_utils.transform_schema_gear_to_model_gear")
    def test_db_error(self, mock_transform, mock_get_by_nick, mock_db):
        import gears.gear.crud as crud
        import gears.gear.schema as s

        mock_get_by_nick.return_value = None
        mock_transform.return_value = MagicMock()
        mock_db.add.side_effect = SQLAlchemyError("err")

        gear = s.GearCreate(nickname="New Gear", gear_type=1)
        with pytest.raises(HTTPException) as e:
            crud.create_gear(gear=gear, user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestEditGear:
    def test_success(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        db_gear = MagicMock(spec=m.Gear)
        db_gear.id = 1
        setup_mock_execute(mock_db, return_one_or_none=db_gear)

        from pydantic import BaseModel

        class GearUpdate(BaseModel):
            id: int = 1
            nickname: str = "Updated+Bike"
            brand: str = "Trek"
            model: str = "Domane"
            gear_type: int = 1
            active: bool = True
            initial_kms: float = 100.0
            purchase_value: float = 3000.0
            strava_gear_id: str = "strava_1"
            garminconnect_gear_id: str | None = None
            created_at: str | None = None

        r = crud.edit_gear(gear=GearUpdate(), db=mock_db)
        assert r is db_gear
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(db_gear)

    def test_not_found(self, mock_db):
        import gears.gear.crud as crud

        setup_mock_execute(mock_db, return_one_or_none=None)

        from pydantic import BaseModel

        class GearUpdate(BaseModel):
            id: int = 999
            nickname: str = "Ghost"
            brand: str | None = None

        with pytest.raises(HTTPException) as e:
            crud.edit_gear(gear=GearUpdate(), db=mock_db)
        assert e.value.status_code == 404

    def test_db_error_execute(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")

        from pydantic import BaseModel

        class GearUpdate(BaseModel):
            id: int = 999
            nickname: str = "Ghost"
            brand: str | None = None

        with pytest.raises(HTTPException) as e:
            crud.edit_gear(gear=GearUpdate(), db=mock_db)
        assert e.value.status_code == 500

    def test_db_error_commit(self, mock_db):
        import gears.gear.crud as crud
        import gears.gear.models as m

        db_gear = MagicMock(spec=m.Gear)
        db_gear.id = 1
        setup_mock_execute(mock_db, return_one_or_none=db_gear)
        mock_db.commit.side_effect = SQLAlchemyError("err")

        from pydantic import BaseModel

        class GearUpdate(BaseModel):
            id: int = 1
            nickname: str = "Updated"
            brand: str | None = None
            model: str | None = None
            gear_type: int | None = None
            created_at: object = None
            active: bool | None = None
            initial_kms: float | None = None
            purchase_value: float | None = None
            strava_gear_id: str | None = None
            garminconnect_gear_id: str | None = None

        with pytest.raises(HTTPException) as e:
            crud.edit_gear(gear=GearUpdate(), db=mock_db)
        assert e.value.status_code == 500


class TestDeleteGear:
    def test_success(self, mock_db):
        import gears.gear.crud as crud

        r = MagicMock()
        r.rowcount = 1
        mock_db.execute.return_value = r
        crud.delete_gear(gear_id=1, db=mock_db)
        mock_db.commit.assert_called_once()

    def test_not_found(self, mock_db):
        import gears.gear.crud as crud

        r = MagicMock()
        r.rowcount = 0
        mock_db.execute.return_value = r
        with pytest.raises(HTTPException) as e:
            crud.delete_gear(gear_id=999, db=mock_db)
        assert e.value.status_code == 404

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.delete_gear(gear_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestDeleteAllStravaGearForUser:
    def test_success(self, mock_db):
        import gears.gear.crud as crud

        r = MagicMock()
        r.rowcount = 3
        mock_db.execute.return_value = r
        crud.delete_all_strava_gear_for_user(user_id=1, db=mock_db)
        mock_db.commit.assert_called_once()

    def test_no_deletions(self, mock_db):
        import gears.gear.crud as crud

        r = MagicMock()
        r.rowcount = 0
        mock_db.execute.return_value = r
        crud.delete_all_strava_gear_for_user(user_id=1, db=mock_db)
        mock_db.commit.assert_not_called()

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.delete_all_strava_gear_for_user(user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestDeleteAllGarminconnectGearForUser:
    def test_success(self, mock_db):
        import gears.gear.crud as crud

        r = MagicMock()
        r.rowcount = 2
        mock_db.execute.return_value = r
        crud.delete_all_garminconnect_gear_for_user(user_id=1, db=mock_db)
        mock_db.commit.assert_called_once()

    def test_no_deletions(self, mock_db):
        import gears.gear.crud as crud

        r = MagicMock()
        r.rowcount = 0
        mock_db.execute.return_value = r
        crud.delete_all_garminconnect_gear_for_user(user_id=1, db=mock_db)
        mock_db.commit.assert_not_called()

    def test_db_error(self, mock_db):
        import gears.gear.crud as crud

        mock_db.execute.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.delete_all_garminconnect_gear_for_user(user_id=1, db=mock_db)
        assert e.value.status_code == 500
