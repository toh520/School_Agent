"""FastAPI application factory for the M01 Agent service foundation."""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from agent_service.agent_repository import AgentRecordNotFound, AgentRepository
from agent_service.agent_routes import router as agent_router
from agent_service.agent_service import AgentOrchestrator
from agent_service.config import Settings, get_settings
from agent_service.database import DatabaseHealth, probe_database
from agent_service.identity import CoreIdentityClient, IdentityError
from agent_service.knowledge_rag import KnowledgeRagService
from agent_service.learning_service import LearningAssistantService, LearningRepository
from agent_service.llm import ModelUnavailable, OpenAICompatibleModel
from agent_service.logging_config import configure_logging
from agent_service.middleware import RequestIdMiddleware, request_id_context
from agent_service.schemas import AgentHealth, ApiError, ApiResponse, DatabaseStatus
from agent_service.study_materials import StudyMaterialService
from agent_service.tools import ToolExecutor, build_tool_registry
from agent_service.workflow import IntentRouter, WorkflowEngine

LOGGER = logging.getLogger(__name__)
AGENT_VERSION = "0.2.0"
DatabaseProbe = Callable[[Settings], DatabaseHealth]


def create_app(
    settings: Settings | None = None,
    database_probe: DatabaseProbe = probe_database,
) -> FastAPI:
    """Create an app whose required configuration is validated during startup."""

    configure_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        active_settings = settings or get_settings()
        application.state.settings = active_settings
        application.state.database_probe = database_probe
        application.state.agent_repository = AgentRepository(active_settings)
        application.state.identity_client = CoreIdentityClient(active_settings)
        model = OpenAICompatibleModel(
            active_settings, config_loader=application.state.agent_repository.llm_runtime_config
        )
        application.state.model = model
        application.state.knowledge_rag = KnowledgeRagService(active_settings)
        application.state.study_materials = StudyMaterialService(active_settings)
        application.state.learning_assistant = LearningAssistantService(
            model,
            application.state.study_materials,
            LearningRepository(active_settings),
        )
        registry = build_tool_registry()
        application.state.tool_registry = registry
        application.state.agent_orchestrator = AgentOrchestrator(
            application.state.agent_repository,
            WorkflowEngine(IntentRouter(model), ToolExecutor(registry)),
            model,
            application.state.knowledge_rag,
        )
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
    application.include_router(agent_router)

    def error_response(code: str, message: str, status_code: int) -> JSONResponse:
        response = ApiResponse[None](
            success=False,
            data=None,
            error=ApiError(code=code, message=message),
            request_id=request_id_context.get(),
            timestamp=ApiResponse.ok(None, request_id_context.get()).timestamp,
        )
        return JSONResponse(
            status_code=status_code, content=response.model_dump(mode="json", by_alias=True)
        )

    @application.exception_handler(IdentityError)
    async def handle_identity(request: Request, exception: IdentityError) -> JSONResponse:
        del request
        code = str(exception)
        if code == "FORBIDDEN":
            return error_response(code, "当前账号无权使用学生智能服务", 403)
        if code == "IDENTITY_UNAVAILABLE":
            return error_response(code, "身份服务暂时不可用", 503)
        return error_response("UNAUTHENTICATED", "登录状态已失效", 401)

    @application.exception_handler(AgentRecordNotFound)
    async def handle_not_found(request: Request, exception: AgentRecordNotFound) -> JSONResponse:
        del request
        return error_response(str(exception), "记录不存在或不属于当前用户", 404)

    @application.exception_handler(PermissionError)
    async def handle_permission(request: Request, exception: PermissionError) -> JSONResponse:
        del request
        code = str(exception)
        message = "需要明确确认后才能保存长期偏好"
        if code == "DATA_SCOPE_DENIED":
            message = "请先在数据授权中开启对应权限"
        return error_response(code, message, 403)

    @application.exception_handler(ModelUnavailable)
    async def handle_model_unavailable(
        request: Request, exception: ModelUnavailable
    ) -> JSONResponse:
        del request, exception
        return error_response("MODEL_UNAVAILABLE", "AI 推荐暂时不可用，请稍后重试", 503)

    @application.exception_handler(ValueError)
    async def handle_invalid_result(request: Request, exception: ValueError) -> JSONResponse:
        del request
        return error_response("INVALID_REQUEST", str(exception), 400)

    @application.exception_handler(Exception)
    async def handle_unexpected(request: Request, exception: Exception) -> JSONResponse:
        LOGGER.error("Unhandled request failure: %s", exception.__class__.__name__)
        return error_response("INTERNAL_ERROR", "服务内部错误", 500)

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
