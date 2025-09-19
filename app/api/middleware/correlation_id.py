"""Middleware pour propager un identifiant de corrélation par requête."""

from __future__ import annotations

from typing import Callable
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Injecte un identifiant de corrélation dans l'état de la requête."""

    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        incoming_id = request.headers.get(self.header_name)
        trace_id = incoming_id or str(uuid4())
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers.setdefault(self.header_name, trace_id)
        return response
