from types import SimpleNamespace

import httpx
import pytest

from agent_service.identity import CoreIdentityClient

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_loopback_identity_lookup_ignores_environment_proxy(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def get(self, *_args, **_kwargs):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "profile": {
                            "id": "955f5cf8-649b-4e26-a85f-f617e203006a",
                            "role": "STUDENT",
                        },
                        "authorizations": {},
                    }
                },
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    settings = SimpleNamespace(core_url="http://127.0.0.1:8080")

    identity = await CoreIdentityClient(settings).resolve("Bearer local-token", "request-id")

    assert identity.role == "STUDENT"
    assert captured["trust_env"] is False
