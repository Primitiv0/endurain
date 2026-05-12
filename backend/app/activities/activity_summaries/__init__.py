"""
Activity summaries sub-module for aggregated metrics.

This module provides summary aggregations of activity data
across different time periods (weekly, monthly, yearly,
lifetime) with breakdowns by day, week, month, year, and
activity type.

Exports:
    - CRUD: get_weekly_summary, get_monthly_summary,
      get_yearly_summary, get_lifetime_summary
    - Schemas: SummaryMetrics, DaySummary, WeekSummary,
      MonthSummary, YearlyPeriodSummary,
      TypeBreakdownItem, WeeklySummaryResponse,
      MonthlySummaryResponse, YearlySummaryResponse,
      LifetimeSummaryResponse
    - Dependencies: validate_view_type
"""

from .crud import (
    get_weekly_summary,
    get_monthly_summary,
    get_yearly_summary,
    get_lifetime_summary,
)
from .schema import (
    SummaryMetrics,
    DaySummary,
    WeekSummary,
    MonthSummary,
    YearlyPeriodSummary,
    TypeBreakdownItem,
    WeeklySummaryResponse,
    MonthlySummaryResponse,
    YearlySummaryResponse,
    LifetimeSummaryResponse,
)
from .dependencies import validate_view_type

__all__ = [
    # CRUD operations
    "get_weekly_summary",
    "get_monthly_summary",
    "get_yearly_summary",
    "get_lifetime_summary",
    # Pydantic schemas
    "SummaryMetrics",
    "DaySummary",
    "WeekSummary",
    "MonthSummary",
    "YearlyPeriodSummary",
    "TypeBreakdownItem",
    "WeeklySummaryResponse",
    "MonthlySummaryResponse",
    "YearlySummaryResponse",
    "LifetimeSummaryResponse",
    # Dependencies
    "validate_view_type",
]
