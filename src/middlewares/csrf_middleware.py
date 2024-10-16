import logging

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

from src.config import settings
from src.services.sessions import SessionsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware for CSRF protection using the Synchronizer Token Pattern.

    This middleware validates CSRF tokens on unsafe method requests by comparing
    the token provided in the request headers with the token stored in the user's session.
    """

    def __init__(
        self,
        app: FastAPI,
        sessions_service: SessionsService,
        csrf_header_name: str = "X-CSRF-Token",
    ):
        """
        Initialize the CSRFMiddleware.

        :param app: The FastAPI application instance.
        :param sessions_service: A service for interacting with sessions.
        :param csrf_header_name: The name of the HTTP header for CSRF token.
        """
        super().__init__(app)
        self.sessions_service = sessions_service
        self.csrf_header_name = csrf_header_name

    async def dispatch(self, request: Request, call_next):
        """
        Process incoming requests to validate CSRF tokens.

        :param request: The incoming HTTP request.
        :param call_next: The next middleware or route handler.
        :return: The HTTP response after CSRF validation.
        """
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            # Safe methods do not require CSRF validation
            response = await call_next(request)
            return response

        session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if not session_id:
            logger.error("Session ID not found in cookies.")
            return PlainTextResponse("Not authenticated", status_code=401)

        csrf_token = await self.sessions_service.get_csrf_token(session_id)
        if not csrf_token:
            logger.error("CSRF token not found in session.")
            return PlainTextResponse("CSRF token missing", status_code=403)

        csrf_token_from_header = request.headers.get(self.csrf_header_name)
        if not csrf_token_from_header:
            logger.error("CSRF token not found in headers.")
            return PlainTextResponse("CSRF token missing in headers", status_code=403)

        if csrf_token != csrf_token_from_header:
            logger.error("Invalid CSRF token.")
            return PlainTextResponse("Forbidden", status_code=403)

        response = await call_next(request)
        return response
