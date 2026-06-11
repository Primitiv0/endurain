from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from tests._helpers.db import setup_mock_execute
from tests._helpers.models import mock_model


class TestCreateActivityStreams:
    @patch("activities.activity_streams.crud.activity_streams_models.ActivityStreams")
    def test_success(self, mock_streams_model, mock_db):
        import activities.activity_streams.crud as crud
        from activities.activity_streams.schema import ActivityStreams

        mock_streams_model.return_value = MagicMock()
        s = [
            ActivityStreams(
                activity_id=1, stream_type=1, stream_waypoints=[{"hr": 145}], strava_activity_stream_id=None
            )
        ]
        crud.create_activity_streams(s, mock_db)
        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_empty(self, mock_db):
        import activities.activity_streams.crud as crud

        crud.create_activity_streams([], mock_db)

    @patch("activities.activity_streams.crud.activity_streams_models.ActivityStreams")
    def test_db_error(self, mock_streams_model, mock_db):
        import activities.activity_streams.crud as crud
        from activities.activity_streams.schema import ActivityStreams

        mock_streams_model.return_value = MagicMock()
        mock_db.commit.side_effect = SQLAlchemyError("err")
        s = [ActivityStreams(activity_id=1, stream_type=1, stream_waypoints=[], strava_activity_stream_id=None)]
        with pytest.raises(HTTPException) as e:
            crud.create_activity_streams(s, mock_db)
        assert e.value.status_code == 500


class TestGetActivityStreams:
    @patch("activities.activity_streams.crud.activity_streams_utils.transform_activity_streams")
    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_success(self, mock_get_act, mock_transform, mock_db):
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m
        from activities.activity_streams.schema import ActivityStreams

        mock_get_act.return_value = MagicMock(user_id=1)
        mock_transform.return_value = ActivityStreams(
            activity_id=1, stream_type=1, stream_waypoints=[], strava_activity_stream_id=None
        )
        setup_mock_execute(
            mock_db, return_scalars_all=[mock_model(m.ActivityStreams, id=1, activity_id=1, stream_type=1)]
        )
        r = crud.get_activity_streams(activity_id=1, token_user_id=1, db=mock_db)
        assert len(r) == 1

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    @patch("activities.activity_streams.crud.activity_streams_schema.ActivityStreams.model_validate")
    def test_by_type(self, mock_validate, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m
        from activities.activity_streams.schema import ActivityStreams

        mock_get_act.return_value = MagicMock(user_id=1)
        mock_validate.return_value = ActivityStreams(
            activity_id=1, stream_type=1, stream_waypoints=[], strava_activity_stream_id=None
        )
        setup_mock_execute(
            mock_db, return_one_or_none=mock_model(m.ActivityStreams, id=1, activity_id=1, stream_type=1)
        )
        r = crud.get_activity_stream_by_type(activity_id=1, stream_type=1, token_user_id=1, db=mock_db)
        assert r is not None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_not_found(self, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_get_act.return_value = None
        r = crud.get_activity_streams(activity_id=1, token_user_id=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_streams_utils.transform_activity_streams")
    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_empty(self, mock_get_act, mock_transform, mock_db):
        import activities.activity_streams.crud as crud

        mock_get_act.return_value = MagicMock(user_id=1)
        mock_db.scalars.return_value.all.return_value = []
        r = crud.get_activity_streams(activity_id=1, token_user_id=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_streams_utils.filter_visible_streams")
    @patch("activities.activity_streams.crud.activity_streams_utils.transform_activity_streams")
    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_non_owner(self, mock_get_act, mock_transform, mock_filter, mock_db):
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m

        mock_get_act.return_value = MagicMock(user_id=2)
        mock_filter.return_value = [MagicMock(spec=m.ActivityStreams)]
        mock_transform.return_value = MagicMock()
        mock_db.scalars.return_value.all.return_value = [MagicMock(spec=m.ActivityStreams, id=1, activity_id=1)]
        r = crud.get_activity_streams(activity_id=1, token_user_id=1, db=mock_db)
        assert len(r) == 1

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_db_error(self, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_get_act.return_value = MagicMock(user_id=1)
        mock_db.scalars.return_value.all.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_activity_streams(activity_id=1, token_user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetActivitiesStreams:
    @patch("activities.activity_streams.crud.activity_streams_utils.transform_activity_streams")
    def test_success(self, mock_transform, mock_db):
        import activities.activity.models as am
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m

        mock_transform.return_value = MagicMock()
        mock_activity = MagicMock(spec=am.Activity, id=1, user_id=1)
        mock_stream = MagicMock(spec=m.ActivityStreams, id=1, activity_id=1)
        mock_db.scalars.return_value.all.side_effect = [
            [mock_activity],
            [mock_stream],
        ]
        r = crud.get_activities_streams(activity_ids=[1], token_user_id=1, db=mock_db)
        assert len(r) == 1

    def test_empty_ids(self, mock_db):
        import activities.activity_streams.crud as crud

        r = crud.get_activities_streams(activity_ids=[], token_user_id=1, db=mock_db)
        assert r == []

    def test_no_activities(self, mock_db):
        import activities.activity_streams.crud as crud

        mock_db.scalars.return_value.all.return_value = []
        r = crud.get_activities_streams(activity_ids=[1], token_user_id=1, db=mock_db)
        assert r == []

    def test_no_allowed(self, mock_db):
        import activities.activity.models as am
        import activities.activity_streams.crud as crud

        mock_activity = MagicMock(spec=am.Activity, id=1, user_id=2)
        mock_db.scalars.return_value.all.return_value = [mock_activity]
        r = crud.get_activities_streams(activity_ids=[1], token_user_id=1, db=mock_db)
        assert r == []

    def test_no_streams(self, mock_db):
        import activities.activity.models as am
        import activities.activity_streams.crud as crud

        mock_activity = MagicMock(spec=am.Activity, id=1, user_id=1)
        mock_db.scalars.return_value.all.side_effect = [
            [mock_activity],
            [],
        ]
        r = crud.get_activities_streams(activity_ids=[1], token_user_id=1, db=mock_db)
        assert r == []

    def test_db_error(self, mock_db):
        import activities.activity_streams.crud as crud

        mock_db.scalars.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_activities_streams(activity_ids=[1], token_user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetPublicActivityStreams:
    @patch("activities.activity_streams.crud.activity_streams_utils.filter_visible_streams")
    @patch("activities.activity_streams.crud.activity_streams_utils.transform_activity_streams")
    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_success(self, mock_settings, mock_get_act, mock_transform, mock_filter, mock_db):
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = MagicMock()
        mock_transform.return_value = MagicMock()
        mock_filter.return_value = [MagicMock(spec=m.ActivityStreams)]
        mock_db.scalars.return_value.all.return_value = [MagicMock(spec=m.ActivityStreams, id=1)]
        r = crud.get_public_activity_streams(activity_id=1, db=mock_db)
        assert len(r) == 1

    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_no_public_links(self, mock_settings, mock_db):
        import activities.activity_streams.crud as crud

        mock_settings.return_value = MagicMock(public_shareable_links=False)
        r = crud.get_public_activity_streams(activity_id=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_not_found(self, mock_settings, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = None
        r = crud.get_public_activity_streams(activity_id=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_no_streams(self, mock_settings, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = MagicMock()
        mock_db.scalars.return_value.all.return_value = []
        r = crud.get_public_activity_streams(activity_id=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_db_error(self, mock_settings, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = MagicMock()
        mock_db.scalars.return_value.all.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_public_activity_streams(activity_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetActivityStreamByType:
    @patch("activities.activity_streams.crud.activity_streams_utils.transform_activity_streams")
    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_success(self, mock_get_act, mock_transform, mock_db):
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m

        mock_get_act.return_value = MagicMock(user_id=1)
        mock_transform.return_value = MagicMock()
        mock_db.scalars.return_value.first.return_value = MagicMock(spec=m.ActivityStreams, id=1, stream_type=1)
        r = crud.get_activity_stream_by_type(activity_id=1, stream_type=1, token_user_id=1, db=mock_db)
        assert r is not None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_not_found(self, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_get_act.return_value = None
        r = crud.get_activity_stream_by_type(activity_id=1, stream_type=1, token_user_id=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_empty(self, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_get_act.return_value = MagicMock(user_id=1)
        mock_db.scalars.return_value.first.return_value = None
        r = crud.get_activity_stream_by_type(activity_id=1, stream_type=1, token_user_id=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_streams_utils.is_stream_hidden")
    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_hidden(self, mock_get_act, mock_hidden, mock_db):
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m

        mock_get_act.return_value = MagicMock(user_id=2)
        mock_hidden.return_value = True
        mock_db.scalars.return_value.first.return_value = MagicMock(spec=m.ActivityStreams, id=1, stream_type=1)
        r = crud.get_activity_stream_by_type(activity_id=1, stream_type=1, token_user_id=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id")
    def test_db_error(self, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_get_act.return_value = MagicMock(user_id=1)
        mock_db.scalars.return_value.first.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_activity_stream_by_type(activity_id=1, stream_type=1, token_user_id=1, db=mock_db)
        assert e.value.status_code == 500


class TestGetPublicActivityStreamByType:
    @patch("activities.activity_streams.crud.activity_streams_utils.transform_activity_streams")
    @patch("activities.activity_streams.crud.activity_streams_utils.is_stream_hidden")
    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_success(self, mock_settings, mock_get_act, mock_hidden, mock_transform, mock_db):
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = MagicMock()
        mock_hidden.return_value = False
        mock_transform.return_value = MagicMock()
        mock_db.scalars.return_value.first.return_value = MagicMock(spec=m.ActivityStreams, id=1, stream_type=1)
        r = crud.get_public_activity_stream_by_type(activity_id=1, stream_type=1, db=mock_db)
        assert r is not None

    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_no_public_links(self, mock_settings, mock_db):
        import activities.activity_streams.crud as crud

        mock_settings.return_value = MagicMock(public_shareable_links=False)
        r = crud.get_public_activity_stream_by_type(activity_id=1, stream_type=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_not_found(self, mock_settings, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = None
        r = crud.get_public_activity_stream_by_type(activity_id=1, stream_type=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_no_stream(self, mock_settings, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = MagicMock()
        mock_db.scalars.return_value.first.return_value = None
        r = crud.get_public_activity_stream_by_type(activity_id=1, stream_type=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_streams_utils.is_stream_hidden")
    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_hidden(self, mock_settings, mock_get_act, mock_hidden, mock_db):
        import activities.activity_streams.crud as crud
        import activities.activity_streams.models as m

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = MagicMock()
        mock_hidden.return_value = True
        mock_db.scalars.return_value.first.return_value = MagicMock(spec=m.ActivityStreams, id=1, stream_type=1)
        r = crud.get_public_activity_stream_by_type(activity_id=1, stream_type=1, db=mock_db)
        assert r is None

    @patch("activities.activity_streams.crud.activity_crud.get_activity_by_id_if_is_public")
    @patch("activities.activity_streams.crud.server_settings_utils.get_server_settings_or_404")
    def test_db_error(self, mock_settings, mock_get_act, mock_db):
        import activities.activity_streams.crud as crud

        mock_settings.return_value = MagicMock(public_shareable_links=True)
        mock_get_act.return_value = MagicMock()
        mock_db.scalars.return_value.first.side_effect = SQLAlchemyError("err")
        with pytest.raises(HTTPException) as e:
            crud.get_public_activity_stream_by_type(activity_id=1, stream_type=1, db=mock_db)
        assert e.value.status_code == 500
