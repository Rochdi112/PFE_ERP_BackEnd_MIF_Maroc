# app/core/ratelimit.py

from collections import defaultdict
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

WINDOW = 60  # fenêtre en secondes
LIMIT = 120  # requêtes par fenêtre
_hits = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ip = request.client.host
        now = time()
        _hits[ip] = [t for t in _hits[ip] if now - t < WINDOW] + [now]
        if len(_hits[ip]) > LIMIT:
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
        return await call_next(request)
