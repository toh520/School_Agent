"""Central identity validation through the Java service's revocable session boundary."""

from typing import Any

import httpx

from agent_service.agent_models import IdentityContext
from agent_service.config import Settings
from agent_service.middleware import REQUEST_ID_HEADER


class IdentityError(RuntimeError):
    """Raised when the bearer token is absent, invalid, or not a student token."""


class CoreIdentityClient:
    """Resolve identity and data grants without sharing JWT secrets with the Agent service."""

    def __init__(self, settings: Settings) -> None:
        self._core_url = settings.core_url.rstrip("/")

    async def resolve(self, authorization: str | None, request_id: str) -> IdentityContext:
        if not authorization or not authorization.startswith("Bearer "):
            raise IdentityError("UNAUTHENTICATED")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self._core_url}/api/v1/users/me",
                    headers={"Authorization": authorization, REQUEST_ID_HEADER: request_id},
                )
        except httpx.HTTPError as exception:
            raise IdentityError("IDENTITY_UNAVAILABLE") from exception
        if response.status_code != 200:
            raise IdentityError("UNAUTHENTICATED" if response.status_code == 401 else "FORBIDDEN")
        payload: dict[str, Any] = response.json().get("data") or {}
        profile = payload.get("profile") or {}
        if profile.get("role") != "STUDENT":
            raise IdentityError("FORBIDDEN")
        authorizations = {
            scope: bool(item.get("granted"))
            for scope, item in (payload.get("authorizations") or {}).items()
        }
        return IdentityContext(
            user_id=profile["id"], role=profile["role"], authorizations=authorizations
        )
