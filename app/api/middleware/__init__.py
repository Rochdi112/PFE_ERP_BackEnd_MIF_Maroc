"""Composants applicatifs partagés (middleware, handlers d'erreurs)."""

from .correlation_id import CorrelationIdMiddleware
from .error_handler import register_exception_handlers

__all__ = ["CorrelationIdMiddleware", "register_exception_handlers"]
