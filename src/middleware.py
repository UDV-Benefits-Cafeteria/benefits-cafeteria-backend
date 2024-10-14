from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.config import settings
from src.services.sessions import SessionsService


class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware which implements the functionality of sliding sessions.

    This middleware checks the presence of a session cookie.
    If a valid session is found and the time since the last update exceeds
    the refresh threshold, the session expiration time is updated to be
    exactly like session expire time variable set in config
    and the cookie is reset with the same time.
    """

    def __init__(
        self,
        app: FastAPI,
        sessions_service: SessionsService,
        session_expire_time: int,
        refresh_threshold: int,
    ):
        """
        Initialization of SessionMiddleware.

        :param app: Instance of FastAPI.
        :param sessions_service: A service for interacting with sessions.
        :param session_expire_time: Total lifetime of session in seconds.
        :param refresh_threshold: Threshold in seconds for updating the session expiration.
        """
        super().__init__(app)
        self.sessions_service = sessions_service
        self.session_expire_time = session_expire_time
        self.refresh_threshold = timedelta(seconds=refresh_threshold)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the incoming request and update the session expiration.

        Steps:
            1. Passing the request to the next handler and receiving a response.
            2. Extracting the session_id from the request cookie.
            3. If the session_id is missing, the response is returned unchanged.
            4. Getting a session from the database using sessions_service.
            5. If the session is not found, the response is returned unchanged.
            6. Calculating the time since the last session update.
            7. If time exceeding the threshold has passed, update the session expiration time.
            8. Reset cookies with a new expiration time.


        :param request: An incoming HTTP request.
        :param call_next: A function to pass the request to the next handler.

        :return Response: HTTP response after a session update.
        """
        response: Response = await call_next(request)

        session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if not session_id:
            return response

        session = await self.sessions_service.get_session(session_id)
        if not session:
            return response

        now = datetime.now(timezone.utc)

        session_expiration_timedelta = timedelta(seconds=self.session_expire_time)

        last_refreshed_at = session.expires_at - session_expiration_timedelta

        time_since_last_refresh = now - last_refreshed_at

        if time_since_last_refresh >= self.refresh_threshold:
            new_expires_at = now + session_expiration_timedelta

            success = await self.sessions_service.update_session_expiration(
                session_id, new_expires_at
            )

            if success:
                response.set_cookie(
                    key=settings.SESSION_COOKIE_NAME,
                    value=session_id,
                    max_age=self.session_expire_time,
                    httponly=True,
                    samesite="lax",
                    secure=False,  # needs to be set True in prod
                )

        return response
