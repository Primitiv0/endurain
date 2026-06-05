from datetime import date as date_class
from datetime import timedelta
from unittest.mock import MagicMock, patch


class TestCalculateStreaks:
    def test_no_completed_fasts(self, mock_db):
        from health.health_fasting.utils import calculate_streaks

        with patch(
            "health.health_fasting.utils.health_fasting_crud.get_completed_fasting_ordered_by_date_and_user_id"
        ) as m:
            m.return_value = []
            current, longest = calculate_streaks(1, mock_db)
            assert current == 0
            assert longest == 0

    def test_empty_dates_list(self, mock_db):
        from health.health_fasting.utils import calculate_streaks

        with patch(
            "health.health_fasting.utils.health_fasting_crud.get_completed_fasting_ordered_by_date_and_user_id"
        ) as m:
            m.return_value = [MagicMock(fast_start_time=None)]
            current, longest = calculate_streaks(1, mock_db)
            assert current == 0
            assert longest == 1

    def test_single_day(self, mock_db):
        from health.health_fasting.utils import calculate_streaks

        fast = MagicMock()
        fast.fast_start_time = date_class(2024, 1, 15)

        with patch(
            "health.health_fasting.utils.health_fasting_crud.get_completed_fasting_ordered_by_date_and_user_id"
        ) as m:
            m.return_value = [fast]
            current, longest = calculate_streaks(1, mock_db)
            assert current == 0  # not today or yesterday
            assert longest == 1

    def test_consecutive_days(self, mock_db):
        from health.health_fasting.utils import calculate_streaks

        today = date_class.today()
        fasts = [
            MagicMock(fast_start_time=today - timedelta(days=2)),
            MagicMock(fast_start_time=today - timedelta(days=1)),
            MagicMock(fast_start_time=today),
        ]

        with patch(
            "health.health_fasting.utils.health_fasting_crud.get_completed_fasting_ordered_by_date_and_user_id"
        ) as m:
            m.return_value = fasts
            current, longest = calculate_streaks(1, mock_db)
            assert current == 3
            assert longest == 3

    def test_current_streak_active_yesterday(self, mock_db):
        from health.health_fasting.utils import calculate_streaks

        today = date_class.today()
        fasts = [
            MagicMock(fast_start_time=today - timedelta(days=3)),
            MagicMock(fast_start_time=today - timedelta(days=2)),
            MagicMock(fast_start_time=today - timedelta(days=1)),
        ]

        with patch(
            "health.health_fasting.utils.health_fasting_crud.get_completed_fasting_ordered_by_date_and_user_id"
        ) as m:
            m.return_value = fasts
            current, longest = calculate_streaks(1, mock_db)
            assert current == 3
            assert longest == 3

    def test_broken_streak(self, mock_db):
        from health.health_fasting.utils import calculate_streaks

        today = date_class.today()
        fasts = [
            MagicMock(fast_start_time=today - timedelta(days=5)),
            MagicMock(fast_start_time=today - timedelta(days=4)),
            MagicMock(fast_start_time=today - timedelta(days=2)),
            MagicMock(fast_start_time=today - timedelta(days=1)),
        ]

        with patch(
            "health.health_fasting.utils.health_fasting_crud.get_completed_fasting_ordered_by_date_and_user_id"
        ) as m:
            m.return_value = fasts
            current, longest = calculate_streaks(1, mock_db)
            assert current == 2  # last 2 days
            assert longest == 2  # both streaks are length 2

    def test_not_current_streak(self, mock_db):
        from health.health_fasting.utils import calculate_streaks

        today = date_class.today()
        fasts = [
            MagicMock(fast_start_time=today - timedelta(days=4)),
            MagicMock(fast_start_time=today - timedelta(days=3)),
            MagicMock(fast_start_time=today - timedelta(days=2)),
        ]

        with patch(
            "health.health_fasting.utils.health_fasting_crud.get_completed_fasting_ordered_by_date_and_user_id"
        ) as m:
            m.return_value = fasts
            current, longest = calculate_streaks(1, mock_db)
            assert current == 0  # last fast was 2 days ago
            assert longest == 3
