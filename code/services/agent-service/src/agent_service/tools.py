"""Permission-aware tool contracts and the M04 test-stub registry."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import monotonic
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from agent_service.agent_models import IdentityContext, ToolCallTrace

ToolHandler = Callable[[BaseModel, IdentityContext], Awaitable[dict[str, Any]]]


class ToolDenied(RuntimeError):
    """Raised before a handler runs when role or data authorization is insufficient."""


class ToolArgumentsInvalid(RuntimeError):
    """Raised when model-produced arguments do not satisfy the registered schema."""


class ContextSnapshotArguments(BaseModel):
    intent: str = Field(min_length=1, max_length=24)
    conditions: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class ToolDefinition:
    """Complete auditable contract required before any Agent tool can execute."""

    name: str
    version: str
    purpose: str
    input_model: type[BaseModel]
    output_schema: dict[str, Any]
    required_role: str
    required_scope: str | None
    timeout_seconds: float
    access_level: Literal["READ", "WRITE"]
    idempotent: bool
    error_types: tuple[str, ...]
    audit_fields: tuple[str, ...]
    handler: ToolHandler

    @property
    def input_schema(self) -> dict[str, Any]:
        return self.input_model.model_json_schema()


class ToolRegistry:
    def __init__(self, definitions: list[ToolDefinition]) -> None:
        self._definitions = {definition.name: definition for definition in definitions}

    def get(self, name: str) -> ToolDefinition:
        if name not in self._definitions:
            raise ToolArgumentsInvalid("TOOL_NOT_REGISTERED")
        return self._definitions[name]

    def public_contracts(self) -> list[dict[str, Any]]:
        """Expose contracts without executable handlers or private runtime values."""

        return [
            {
                "name": item.name,
                "version": item.version,
                "purpose": item.purpose,
                "inputSchema": item.input_schema,
                "outputSchema": item.output_schema,
                "requiredRole": item.required_role,
                "requiredScope": item.required_scope,
                "timeoutSeconds": item.timeout_seconds,
                "accessLevel": item.access_level,
                "idempotent": item.idempotent,
                "errorTypes": item.error_types,
                "auditFields": item.audit_fields,
            }
            for item in self._definitions.values()
        ]


class ToolExecutor:
    """Validate identity and arguments outside the model before bounded execution."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(
        self, name: str, arguments: dict[str, Any], identity: IdentityContext
    ) -> ToolCallTrace:
        definition = self._registry.get(name)
        started = monotonic()
        try:
            if identity.role != definition.required_role:
                raise ToolDenied("ROLE_DENIED")
            if definition.required_scope and not identity.authorizations.get(
                definition.required_scope, False
            ):
                raise ToolDenied("DATA_SCOPE_DENIED")
            try:
                parsed = definition.input_model.model_validate(arguments)
            except ValidationError as exception:
                raise ToolArgumentsInvalid("INVALID_TOOL_ARGUMENTS") from exception
            result = await asyncio.wait_for(
                definition.handler(parsed, identity), timeout=definition.timeout_seconds
            )
            return ToolCallTrace(
                toolName=definition.name,
                toolVersion=definition.version,
                arguments=parsed.model_dump(mode="json"),
                result=result,
                status="SUCCESS",
                durationMs=round((monotonic() - started) * 1000),
            )
        except ToolDenied as exception:
            return ToolCallTrace(
                toolName=definition.name,
                toolVersion=definition.version,
                arguments=arguments,
                result=None,
                status="DENIED",
                errorType=str(exception),
                durationMs=round((monotonic() - started) * 1000),
            )
        except (ToolArgumentsInvalid, TimeoutError) as exception:
            error_type = "TOOL_TIMEOUT" if isinstance(exception, TimeoutError) else str(exception)
            return ToolCallTrace(
                toolName=definition.name,
                toolVersion=definition.version,
                arguments=arguments,
                result=None,
                status="FAILED",
                errorType=error_type,
                durationMs=round((monotonic() - started) * 1000),
            )


async def context_snapshot(arguments: BaseModel, identity: IdentityContext) -> dict[str, Any]:
    """Return only caller-supplied conditions; M04 intentionally has no domain data access."""

    parsed = ContextSnapshotArguments.model_validate(arguments.model_dump())
    return {
        "intent": parsed.intent,
        "conditions": parsed.conditions,
        "owner": str(identity.user_id),
        "source": "current conversation",
    }


def build_tool_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            ToolDefinition(
                name="context_snapshot",
                version="1.0.0",
                purpose="Validate and echo the current conversation conditions for workflow tests",
                input_model=ContextSnapshotArguments,
                output_schema={"type": "object", "required": ["intent", "conditions", "source"]},
                required_role="STUDENT",
                required_scope=None,
                timeout_seconds=2.0,
                access_level="READ",
                idempotent=True,
                error_types=("ROLE_DENIED", "INVALID_TOOL_ARGUMENTS", "TOOL_TIMEOUT"),
                audit_fields=("user_id", "request_id", "tool_name", "status", "duration_ms"),
                handler=context_snapshot,
            )
        ]
    )
