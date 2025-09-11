# app/api/v1/__init__.py

from . import (
    auth,
    dashboard,
    documents,
    equipements,
    filters,
    health,
    interventions,
    notifications,
    planning,
    techniciens,
    users,
)

__all__ = [
    "auth",
    "users",
    "techniciens",
    "equipements",
    "interventions",
    "planning",
    "notifications",
    "documents",
    "filters",
    "dashboard",
    "health",
]
