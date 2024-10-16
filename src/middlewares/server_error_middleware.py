import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CatchServerErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch all unhandled exceptions (500 errors) and return a
    unified JSON response instead of exposing the full stack trace.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Internal Server Error: {exc}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error. Please try again later."},
            )
