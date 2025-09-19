"""Gestion centralisée des erreurs HTTP pour l'API."""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

_LOGGER = logging.getLogger("app.error")

_STATUS_CODE_MAPPING: Dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "RESOURCE_NOT_FOUND",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
}


def _build_error_payload(
    *,
    code: str,
    message: str,
    trace_id: str,
    details: Any = None,
) -> Dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "trace_id": trace_id,
        }
    }


def _extract_message_and_details(detail: Any) -> Tuple[str, Any]:
    if isinstance(detail, dict):
        message = (
            detail.get("message")
            or detail.get("detail")
            or detail.get("error")
            or "Erreur"
        )
        return str(message), detail
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail), detail
    if detail is None:
        return "Erreur", None
    return str(detail), None


def _status_to_code(status_code: int) -> str:
    return _STATUS_CODE_MAPPING.get(status_code, "INTERNAL_SERVER_ERROR")


def _ensure_trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None) or request.headers.get(
        "X-Request-ID"
    )
    if not trace_id:
        trace_id = str(uuid4())
    request.state.trace_id = trace_id
    return trace_id


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    trace_id = _ensure_trace_id(request)
    message, details = _extract_message_and_details(exc.detail)
    payload = _build_error_payload(
        code=_status_to_code(exc.status_code),
        message=message,
        trace_id=trace_id,
        details=details if details != message else None,
    )
    headers = dict(exc.headers or {})
    headers["X-Request-ID"] = trace_id
    return JSONResponse(status_code=exc.status_code, content=payload, headers=headers)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    trace_id = _ensure_trace_id(request)
    payload = _build_error_payload(
        code="VALIDATION_ERROR",
        message="Erreur de validation des données",
        trace_id=trace_id,
        details=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload,
        headers={"X-Request-ID": trace_id},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = _ensure_trace_id(request)
    _LOGGER.exception(
        "Unhandled application error", exc_info=exc, extra={"trace_id": trace_id}
    )
    payload = _build_error_payload(
        code="INTERNAL_SERVER_ERROR",
        message="Une erreur interne est survenue.",
        trace_id=trace_id,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload,
        headers={"X-Request-ID": trace_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Enregistre les gestionnaires personnalisés sur l'application FastAPI."""

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
