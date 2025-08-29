# app/api/v1/__init__.py

from . import auth
from . import users
from . import techniciens
from . import equipements
from . import interventions
from . import planning
from . import notifications
from . import documents
from . import filters
from . import dashboard
from . import health

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
    "health"
]
