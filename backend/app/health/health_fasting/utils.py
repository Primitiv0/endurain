from datetime import date, timedelta

from sqlalchemy.orm import Session

import health.health_fasting.crud as health_fasting_crud


def calculate_streaks(user_id: int, db: Session) -> tuple[int, int]:
    """
    Calculate current and longest fasting streaks.

    Args:
        user_id: User ID to calculate streaks for.
        db: Database session.

    Returns:
        Tuple of (current_streak, longest_streak).
    """
    completed_fasts = (
        health_fasting_crud.get_completed_fasting_ordered_by_date_and_user_id(
            user_id, db
        )
    )

    if not completed_fasts:
        return 0, 0

    # Get unique dates
    dates = sorted(set(fast.date for fast in completed_fasts))

    if not dates:
        return 0, 0

    longest_streak = 1
    current_streak = 1
    temp_streak = 1

    for i in range(1, len(dates)):
        if dates[i] - dates[i - 1] == timedelta(days=1):
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1

    # Check if current streak is still active (last fast was today or yesterday)

    today = date.today()
    last_fast_date = dates[-1]

    if last_fast_date == today or last_fast_date == today - timedelta(days=1):
        # Count backwards from the end
        current_streak = 1
        for i in range(len(dates) - 1, 0, -1):
            if dates[i] - dates[i - 1] == timedelta(days=1):
                current_streak += 1
            else:
                break
    else:
        current_streak = 0

    return current_streak, longest_streak
