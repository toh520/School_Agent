"""Request identifier propagation for the Agent service."""

import re
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,80}$")
request_id_context: ContextVar[str] = ContextVar("request_id", default="none")


def normalize_request_id(supplied: str | None) -> str:
    """Keep safe caller IDs and replace malformed values to prevent log injection."""

    if supplied and _SAFE_REQUEST_ID.fullmatch(supplied):
        return supplied
    return str(uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach one identifier to the request context and response headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = normalize_request_id(request.headers.get(REQUEST_ID_HEADER))
        token = request_id_context.set(request_id)
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            request_id_context.reset(token)
