"""
FastAPI router for consolidated health endpoints.

This module provides endpoints that aggregate health data across
multiple health modules for efficient dashboard display.
"""

from datetime import date
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.orm import Session

import health.schema as health_schema

import health.health_sleep.crud as health_sleep_crud
import health.health_weight.crud as health_weight_crud
import health.health_steps.crud as health_steps_crud
import health.health_fasting.crud as health_fasting_crud

import auth.security as auth_security

import core.database as core_database

# Define the API router
router = APIRouter()


@router.get(
    "/stats/daily",
    response_model=health_schema.HealthDashboardResponse,
    status_code=status.HTTP_200_OK,
)
async def read_health_daily_stats(
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:read"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_schema.HealthDashboardResponse:
    """
    Retrieve health daily stats and last weight record.

    Args:
        _check_scopes: Security dependency that validates the user has
            'health:read' scope.
        token_user_id: The ID of the authenticated user extracted from the
            access token.
        db: Database session for executing queries.

    Returns:
        HealthDashboardResponse: A consolidated response containing:
            - sleep: Latest sleep record with key metrics
            - weight: Latest weight and BMI data
            - steps: Today's step count
            - fasting: Active or most recent fasting session

    Raises:
        HTTPException: If the user lacks required 'health:read' scope.
    """
    today = str(date.today())

    # Get today's sleep
    today_sleep = health_sleep_crud.get_health_sleep_by_date_and_user_id(
        token_user_id, today, db
    )

    # Get latest weight (most recent record)
    latest_weight = health_weight_crud.get_latest_weight_by_user_id(token_user_id, db)

    # Get today's steps
    today_steps = health_steps_crud.get_health_steps_by_date_and_user_id(
        token_user_id, today, db
    )

    # Get active fasting or most recent
    active_fasting = health_fasting_crud.get_active_fasting_by_user_id(
        token_user_id, db
    )

    # Build dashboard response with only necessary fields
    sleep_data = None
    if today_sleep:
        sleep_data = health_schema.HealthSleepDashboard(
            total_sleep_seconds=today_sleep.total_sleep_seconds,
            resting_heart_rate=today_sleep.resting_heart_rate,
            hrv_status=today_sleep.hrv_status,
            avg_skin_temp_deviation=today_sleep.avg_skin_temp_deviation,
        )

    weight_data = None
    if latest_weight:
        weight_data = health_schema.HealthWeightDashboard(
            weight=latest_weight.weight,
            bmi=latest_weight.bmi,
        )

    steps_data = None
    if today_steps:
        steps_data = health_schema.HealthStepsDashboard(
            steps=today_steps.steps,
        )

    fasting_data = None
    if active_fasting:
        fasting_data = health_schema.HealthFastingDashboard(
            id=active_fasting.id,
            fast_start_time=active_fasting.fast_start_time,
            fast_end_time=active_fasting.fast_end_time,
            status=active_fasting.status,
            actual_duration_seconds=active_fasting.actual_duration_seconds,
        )

    return health_schema.HealthDashboardResponse(
        sleep=sleep_data,
        weight=weight_data,
        steps=steps_data,
        fasting=fasting_data,
    )
