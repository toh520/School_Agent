"""FastAPI application factory for the M01 Agent service foundation."""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from agent_service.config import Settings, get_settings
from agent_service.database import DatabaseHealth, probe_database
from agent_service.logging_config import configure_logging
from agent_service.middleware import RequestIdMiddleware, request_id_context
from agent_service.schemas import AgentHealth, ApiError, ApiResponse, DatabaseStatus

LOGGER = logging.getLogger(__name__)
AGENT_VERSION = "0.1.0"
DatabaseProbe = Callable[[Settings], DatabaseHealth]


def create_app(
    settings: Settings | None = None,
    database_probe: DatabaseProbe = probe_database,
) -> FastAPI:
    """Create an app whose required configuration is validated during startup."""

    configure_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.settings = settings or get_settings()
        application.state.database_probe = database_probe
        LOGGER.info("Agent foundation started")
        yield
        LOGGER.info("Agent foundation stopped")

    application = FastAPI(
        title="School Agent Service",
        version=AGENT_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    application.add_middleware(RequestIdMiddleware)

    @application.exception_handler(Exception)
    async def handle_unexpected(request: Request, exception: Exception) -> JSONResponse:
        LOGGER.error("Unhandled request failure: %s", exception.__class__.__name__)
        response = ApiResponse[None](
            success=False,
            data=None,
            error=ApiError(code="INTERNAL_ERROR", message="服务内部错误"),
            request_id=request_id_context.get(),
            timestamp=ApiResponse.ok(None, request_id_context.get()).timestamp,
        )
        return JSONResponse(
            status_code=500, content=response.model_dump(mode="json", by_alias=True)
        )

    @application.get("/health", response_model=ApiResponse[AgentHealth])
    async def health(request: Request) -> ApiResponse[AgentHealth]:
        database = await run_in_threadpool(
            request.app.state.database_probe, request.app.state.settings
        )
        data = AgentHealth(
            status="UP",
            version=AGENT_VERSION,
            database=DatabaseStatus(
                status="UP",
                version=(
                    f"PostgreSQL {database.postgres_version} / pgvector {database.vector_version}"
                ),
            ),
        )
        return ApiResponse.ok(data, request_id_context.get())

    return application


app = create_app()
