from uuid import uuid4

import pytest

from agent_service.agent_models import IdentityContext
from agent_service.tools import ToolExecutor, build_tool_registry

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_registered_tool_contract_contains_all_governance_fields() -> None:
    contract = build_tool_registry().public_contracts()[0]

    assert set(contract) == {
        "name",
        "version",
        "purpose",
        "inputSchema",
        "outputSchema",
        "requiredRole",
        "requiredScope",
        "timeoutSeconds",
        "accessLevel",
        "idempotent",
        "errorTypes",
        "auditFields",
    }


@pytest.mark.parametrize("index", range(20))
async def test_stub_tool_success_rate_is_one_hundred_percent(index: int) -> None:
    executor = ToolExecutor(build_tool_registry())
    identity = IdentityContext(user_id=uuid4(), role="STUDENT")

    result = await executor.execute(
        "context_snapshot", {"intent": "FOOD", "conditions": {"index": index}}, identity
    )

    assert result.status == "SUCCESS"
    assert result.result and result.result["conditions"]["index"] == index


async def test_invalid_arguments_and_role_are_blocked_before_handler() -> None:
    executor = ToolExecutor(build_tool_registry())
    student = IdentityContext(user_id=uuid4(), role="STUDENT")
    administrator = IdentityContext(user_id=uuid4(), role="INFO_ADMIN")

    invalid = await executor.execute("context_snapshot", {"conditions": {}}, student)
    denied = await executor.execute(
        "context_snapshot", {"intent": "FOOD", "conditions": {}}, administrator
    )

    assert invalid.status == "FAILED"
    assert invalid.error_type == "INVALID_TOOL_ARGUMENTS"
    assert denied.status == "DENIED"
    assert denied.error_type == "ROLE_DENIED"
