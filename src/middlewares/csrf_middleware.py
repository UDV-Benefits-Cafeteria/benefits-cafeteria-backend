import logging
from secrets import token_urlsafe

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware for CSRF protection.

    This middleware ensures that non-safe HTTP methods (POST, PUT, DELETE, etc.)
    contain a valid CSRF token that matches the one stored in cookies.
    If the token is not found or does not match, the request is rejected with a 403 status.

    For safe methods (GET, HEAD, OPTIONS, TRACE), a new CSRF token is generated if one does not exist.

    CSRF token is stored in cookies, and for non-safe methods, it should also be included
    in either request headers or request body to pass the validation.
    """

    def __init__(
        self,
        app: FastAPI,
        csrf_token_name="csrftoken",
        csrf_token_expiry=10 * 24 * 60 * 60,
    ):
        """
        Initializes the CSRFMiddleware with customizable token name, expiry time, and refresh threshold.

        Steps:
            1. Initialize the BaseHTTPMiddleware with the app.
            2. Set the CSRF token name.
            3. Define the expiration time for the CSRF token.
            4. Define the refresh threshold, the time before expiration when the token should be refreshed.

        :param app: The Starlette/FastAPI application instance.
        :param csrf_token_name: The name of the CSRF token in the cookie (default: 'csrftoken').
        :param csrf_token_expiry: Token expiration time in seconds (default: 10 days).
        """
        super().__init__(app)
        self.CSRF_TOKEN_NAME = csrf_token_name
        self.CSRF_TOKEN_EXPIRY = csrf_token_expiry

    async def dispatch(self, request, call_next):
        """
        Process the incoming request and apply CSRF protection.

        Steps:
            1. Initialize the CSRF token state in the request.
            2. Extract the CSRF token from the request's cookies, headers, or post body.
            3. For unsafe methods (POST, PUT, DELETE), verify that the token from the request matches
               the token from the cookie. If not, return a 403 Forbidden response.
            4. For safe methods (GET, HEAD, OPTIONS, TRACE), check if the token exists.
            5. If no token is found, generate a new one.
            6. If a token exists, calculate the time until expiration.
            7. If the expiration time is close to the threshold, refresh the token.
            8. If a new token is generated or refreshed, set it in the response cookies.
            9. Return the response after applying CSRF validation.

        :param request: The HTTP request being processed.
        :param call_next: A function to pass the request to the next handler.

        :return: A response object, potentially with a new or updated CSRF token in cookies.
        """
        request.state.csrftoken = ""
        token_new_cookie = False
        error_text = (
            "CSRF token validation failed. "
            "The request could not be completed for security reasons. "
            "Please ensure your session is valid and try again."
        )
        token_from_header = request.headers.get(self.CSRF_TOKEN_NAME, None)
        token_from_cookie = request.cookies.get(self.CSRF_TOKEN_NAME, None)
        token_from_post = None

        if hasattr(request.state, "post"):
            token_from_post = request.state.post.get(self.CSRF_TOKEN_NAME, None)

        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            if not token_from_cookie or len(token_from_cookie) < 30:
                logger.error("CSRF Cookie was not set. Aborting request.")
                return PlainTextResponse(error_text, status_code=403)

            if (str(token_from_cookie) != str(token_from_post)) and (
                str(token_from_cookie) != str(token_from_header)
            ):
                logger.error(
                    "CSRF Cookie was not correct. "
                    "Aborting request. "
                    f"Cookie: {token_from_cookie} | Post: {token_from_post} | Header: {token_from_header}"
                )
                return PlainTextResponse(error_text, status_code=403)

        else:
            if not token_from_cookie:
                token_from_cookie = token_urlsafe(32)
                token_new_cookie = True
            else:
                token_new_cookie = False

        request.state.csrftoken = token_from_cookie

        response = await call_next(request)

        if token_new_cookie:
            logger.info("Setting up CSRF Cookie.")
            response.set_cookie(
                self.CSRF_TOKEN_NAME,
                token_from_cookie,
                max_age=self.CSRF_TOKEN_EXPIRY,
                path="/",
                domain=None,
                secure=True,
                httponly=True,
                samesite="strict",
            )

        return response
