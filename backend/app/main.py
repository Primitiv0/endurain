import os
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config

# Silence stravalib token warnings as early as
# possible: this env var is consulted at import time by
# stravalib, so it must be set before any module that
# transitively imports it runs.
os.environ["SILENCE_TOKEN_WARNINGS"] = "TRUE"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

import core.logger as core_logger
import core.config as core_config
import core.scheduler as core_scheduler
import core.tracing as core_tracing
import core.middleware as core_middleware
import core.middleware_request_id as core_middleware_request_id
import core.migrations as core_migrations
import core.rate_limit as core_rate_limit

import garmin.activity_utils as garmin_activity_utils
import garmin.health_utils as garmin_health_utils

import strava.activity_utils as strava_activity_utils
import strava.utils as strava_utils

import password_reset_tokens.utils as password_reset_tokens_utils

import sign_up_tokens.utils as sign_up_tokens_utils

import auth.oauth_state.utils as oauth_state_utils
import auth.idp_link_tokens.utils as idp_link_token_utils

import activities.activity.utils as activities_utils

import server_settings.utils as server_settings_utils
import server_settings.schema as server_settings_schema

from core.database import SessionLocal, engine as core_db_engine
from core.routes import router as api_router


_DEPLOYED_ENVIRONMENTS = {"production", "demo"}


def _safe_run[T, **P](
    label: str,
    func: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T | None:
    """Invoke a startup task, isolating its failure.

    Logs the exception type (not the raw message, to
    avoid leaking sensitive context) so a single
    misbehaving integration cannot abort backend
    startup.
    """
    try:
        return func(*args, **kwargs)
    except Exception as err:
        core_logger.print_to_log(
            f"Startup task '{label}' failed: {type(err).__name__}",
            "error",
            exc=err,
        )
        return None


async def _safe_run_async[T, **P](
    label: str,
    coro_func: Callable[P, Awaitable[T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T | None:
    """Async variant of :func:`_safe_run`."""
    try:
        return await coro_func(*args, **kwargs)
    except Exception as err:
        core_logger.print_to_log(
            f"Startup task '{label}' failed: {type(err).__name__}",
            "error",
            exc=err,
        )
        return None


def _run_alembic_migrations() -> None:
    """Run Alembic upgrade to head.

    Critical: failure here aborts startup because the
    application cannot guarantee schema correctness.
    """
    alembic_cfg = Config("alembic.ini")
    # Disable Alembic's own logger configuration to
    # avoid conflicts with FastAPI / our main logger.
    alembic_cfg.attributes["configure_logger"] = False
    command.upgrade(alembic_cfg, "head")


def _refresh_strava_tokens() -> None:
    """Refresh persisted Strava OAuth tokens."""
    strava_utils.refresh_strava_tokens(True)


async def _retrieve_recent_garmin_activities() -> None:
    """Backfill the last day of Garmin Connect activities."""
    await (
        garmin_activity_utils
        .retrieve_garminconnect_users_activities_for_days(1)
    )


async def _retrieve_recent_strava_activities() -> None:
    """Backfill the last day of Strava activities."""
    await strava_activity_utils.retrieve_strava_users_activities_for_days(
        1,
        True,
    )


async def _retrieve_recent_garmin_health() -> None:
    """Backfill the last day of Garmin Connect health stats."""
    await garmin_health_utils.retrieve_garminconnect_users_health_for_days(1)


def _purge_expired_tokens() -> None:
    """Sweep expired/invalid auth-related tokens from the DB."""
    password_reset_tokens_utils.delete_invalid_tokens_from_db()
    sign_up_tokens_utils.delete_invalid_tokens_from_db()
    oauth_state_utils.delete_expired_oauth_states_from_db()
    idp_link_token_utils.delete_idp_link_expired_tokens_from_db()


def _generate_missing_thumbnails() -> None:
    """Generate map thumbnails for activities missing one."""
    activities_utils.generate_missing_activity_thumbnails()


def _init_allowed_tile_domains(fastapi_app: FastAPI) -> None:
    """Populate ``app.state.allowed_tile_domains`` for CSP.

    Falls back to the built-in default provider list if
    the database lookup fails so the application can
    still serve requests with a safe CSP.
    """
    with SessionLocal() as db:
        try:
            fastapi_app.state.allowed_tile_domains = (
                server_settings_utils.get_allowed_tile_domains(db)
            )
            allowed_tile_domains = fastapi_app.state.allowed_tile_domains
            core_logger.print_to_log_and_console(
                f"Allowed tile domains: {allowed_tile_domains}"
            )
        except Exception as err:
            core_logger.print_to_log(
                "Error initializing tile domains, using defaults: "
                f"{type(err).__name__}",
                "error",
                exc=err,
            )
            # Fallback to built-in providers so CSP
            # remains restrictive but functional.
            fastapi_app.state.allowed_tile_domains = (
                server_settings_schema.DEFAULT_ALLOWED_TILE_DOMAINS.copy()
            )


async def startup_event(fastapi_app: FastAPI) -> None:
    """Run startup tasks in well-defined phases.

    Phase 1 (critical): schema migrations and the
    background scheduler. Failure aborts startup.

    Phase 2 (best-effort): third-party syncs, token
    purges, thumbnail generation, and CSP tile-domain
    initialisation. Each task is isolated so a single
    failure cannot prevent the backend from serving
    requests.
    """
    core_logger.print_to_log_and_console(
        f"Backend startup event - {core_config.API_VERSION}"
    )

    # Phase 1: critical pre-flight tasks.
    _run_alembic_migrations()
    await core_migrations.check_migrations()
    core_scheduler.start_scheduler()

    # Phase 2: best-effort background syncs and clean-up.
    core_logger.print_to_log_and_console("Refreshing Strava tokens on startup")
    _safe_run("refresh_strava_tokens", _refresh_strava_tokens)

    core_logger.print_to_log_and_console(
        "Retrieving last day activities from Garmin Connect on startup"
    )
    await _safe_run_async(
        "retrieve_recent_garmin_activities", _retrieve_recent_garmin_activities
    )

    core_logger.print_to_log_and_console(
        "Retrieving last day activities from Strava on startup"
    )
    await _safe_run_async(
        "retrieve_recent_strava_activities", _retrieve_recent_strava_activities
    )

    core_logger.print_to_log_and_console(
        "Retrieving last day health stats from Garmin Connect on startup"
    )
    await _safe_run_async(
        "retrieve_recent_garmin_health",
        _retrieve_recent_garmin_health,
    )

    core_logger.print_to_log_and_console(
        "Purging expired tokens "
        "(password reset, sign-up, OAuth state, IdP link)"
    )
    _safe_run("purge_expired_tokens", _purge_expired_tokens)

    core_logger.print_to_log_and_console(
        "Generating missing activity map thumbnails"
    )
    _safe_run("generate_missing_thumbnails", _generate_missing_thumbnails)

    core_logger.print_to_log_and_console(
        "Initializing allowed tile domains for Content Security Policy"
    )
    _init_allowed_tile_domains(fastapi_app)

    core_logger.print_to_log_and_console(
        f"Allowed trusted proxies: {core_config.settings.TRUSTED_PROXIES}"
    )


def shutdown_event() -> None:
    """Stop the background scheduler and release DB resources on shutdown."""
    core_logger.print_to_log_and_console("Backend shutdown event")
    core_scheduler.stop_scheduler()

    # Dispose the SQLAlchemy engine so all pooled
    # psycopg connections are closed deterministically.
    try:
        core_db_engine.dispose()
    except Exception as err:
        core_logger.print_to_log_and_console(
            "Error disposing database engine on shutdown: "
            f"{type(err).__name__}",
            "error",
        )


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""
    await startup_event(fastapi_app)
    try:
        yield
    finally:
        shutdown_event()


def create_app() -> FastAPI:
    """Build, configure, and return the FastAPI app.

    Pre-flight: validate required env vars, ensure data
    directories exist, and configure the main logger so
    every subsequent log line is captured by the
    environment-appropriate handler.
    """
    # Pre-flight checks that must run before the app is
    # constructed: required environment variables and
    # filesystem layout. Logger setup must happen after
    # config validation so log routing reflects the
    # validated settings.
    core_config.check_required_env_vars()
    core_config.check_required_dirs()
    core_logger.setup_main_logger()

    is_development = core_config.settings.ENVIRONMENT == "development"
    is_deployed = core_config.settings.ENVIRONMENT in _DEPLOYED_ENVIRONMENTS
    docs_url = f"{core_config.ROOT_PATH}/docs" if is_development else None
    redoc_url = f"{core_config.ROOT_PATH}/redoc" if is_development else None

    # Define the FastAPI object
    fastapi_app = FastAPI(
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        title="Endurain",
        summary="Endurain API for the Endurain app",
        version=core_config.API_VERSION,
        license_info={
            "name": core_config.LICENSE_NAME,
            "identifier": core_config.LICENSE_IDENTIFIER,
            "url": core_config.LICENSE_URL,
        },
    )

    # Add session middleware for OAuth state management
    fastapi_app.add_middleware(
        SessionMiddleware,
        secret_key=core_config.read_secret("SECRET_KEY"),
        session_cookie="endurain_session",
        max_age=3600,  # 1 hour session timeout
        same_site="lax",
        https_only=is_deployed,
    )

    # Add CORS middleware to allow requests from the frontend
    if is_development:
        cors_allow_origins: list[str] = [
            "http://localhost:8080",
            "http://localhost:5173",
            "http://localhost:5174",
            core_config.settings.ENDURAIN_HOST,
        ]
    else:
        cors_allow_origins = [core_config.settings.ENDURAIN_HOST]

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Client-Type",
            "X-CSRF-Token",
        ],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )

    # Add security headers middleware (before CSRF for proper header ordering)
    fastapi_app.add_middleware(core_middleware.SecurityHeadersMiddleware)

    # Add CSRF protection middleware
    fastapi_app.add_middleware(core_middleware.CSRFMiddleware)

    # Add rate limiting
    fastapi_app.state.limiter = core_rate_limit.limiter
    fastapi_app.add_exception_handler(
        core_rate_limit.RateLimitExceeded,
        core_rate_limit.rate_limit_exceeded_handler,  # type: ignore[arg-type]
    )
    fastapi_app.add_middleware(SlowAPIMiddleware)

    # RequestIdMiddleware is added last so it executes
    # first in the request chain, ensuring every log
    # line (including those from other middlewares and
    # error responses) carries an X-Request-ID.
    fastapi_app.add_middleware(
        core_middleware_request_id.RequestIdMiddleware,
    )

    # Static mounts must be registered before the
    # catch-all frontend route included by api_router.
    fastapi_app.mount(
        f"/{core_config.USER_IMAGES_DIR}",
        StaticFiles(directory=core_config.USER_IMAGES_DIR),
        name="user_images",
    )
    fastapi_app.mount(
        f"/{core_config.SERVER_IMAGES_DIR}",
        StaticFiles(directory=core_config.SERVER_IMAGES_DIR),
        name="server_images",
    )
    fastapi_app.mount(
        f"/{core_config.settings.ACTIVITY_MEDIA_DIR}",
        StaticFiles(directory=core_config.settings.ACTIVITY_MEDIA_DIR),
        name="activity_media",
    )
    fastapi_app.mount(
        f"/{core_config.settings.ACTIVITY_THUMBNAILS_DIR}",
        StaticFiles(directory=core_config.settings.ACTIVITY_THUMBNAILS_DIR),
        name="activity_thumbnails",
    )

    # Router files
    fastapi_app.include_router(api_router)

    # Setup tracing once the app and its routes are
    # registered so instrumentation can wrap them.
    core_tracing.setup_tracing(fastapi_app)

    return fastapi_app


# Create the FastAPI application
app = create_app()
