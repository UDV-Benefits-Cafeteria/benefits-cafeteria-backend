from fastapi import Request, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timezone, timedelta
from src.config import settings
from src.services.sessions import SessionsService


class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        sessions_service: SessionsService,
        session_expire_time: int,
        refresh_threshold: int,
    ):
        super().__init__(app)
        self.sessions_service = sessions_service
        self.session_expire_time = session_expire_time
        self.refresh_threshold = timedelta(seconds=refresh_threshold)

    async def dispatch(
        self,
        request: Request,
        call_next
    ) -> Response:

        response: Response = await call_next(request)

        session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if not session_id:
            return response

        session = await self.sessions_service.get_session(session_id)
        if not session:
            return response

        now = datetime.now(timezone.utc)

        session_duration = timedelta(seconds=self.session_expire_time)

        last_refreshed_at = session.expires_at - session_duration

        time_since_last_refresh = now - last_refreshed_at

        if time_since_last_refresh >= self.refresh_threshold:
            new_expires_at = now + session_duration
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
                    secure=False,
                )
        return response
