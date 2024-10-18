from fastapi import APIRouter, HTTPException, Request, Response, status

from src.api.v1.dependencies import (
    AuthServiceDependency,
    SessionsServiceDependency,
    UsersServiceDependency,
)
from src.config import get_settings
from src.schemas.user import UserLogin, UserRegister, UserVerified, UserVerify
from src.services.exceptions import (
    EntityCreateError,
    EntityDeletionError,
    EntityNotFoundError,
    EntityReadError,
    EntityUpdateError,
)
from src.utils.security import verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post(
    "/verify",
    response_model=UserVerified,
    responses={
        200: {"description": "User email verification successful"},
        400: {"description": "User already verified or failed to read user"},
        404: {"description": "User not found"},
    },
)
async def verify_email(
    email_data: UserVerify,
    service: UsersServiceDependency,
):
    """
    Verify the user's email.

    - **email_data**: The user verification data containing the email.

    Raises:
    - **HTTPException**:
        - 400: If the user is already verified or failed to read user.
        - 404: If the user is not found.

    Returns:
    - **UserVerified**: Information about the verified user.
    """
    try:
        user = await service.read_by_email(email_data.email)

        if not user.is_verified:
            return UserVerified(id=user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{email_data.email}' already verified",
            )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email_data.email}' not found",
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read user",
        )


@router.post(
    "/signup",
    responses={
        200: {"description": "User signup and verification successful"},
        404: {"description": "User not found"},
        400: {
            "description": "User already verified, password already set, or failed to update user"
        },
    },
)
async def signup(
    user_register: UserRegister,
    auth_service: AuthServiceDependency,
):
    """
    Sign up a new user and verify their account.

    - **user_register**: The registration data for the user.

    Raises:
    - **HTTPException**:
        - 404: If the user is not found.
        - 400: If the user is already verified, password already set, or failed to update user.

    Returns:
    - **dict**: A dictionary indicating success or failure of the operation.
    """
    try:
        user = await auth_service.read_auth_data(user_id=user_register.id)

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified"
            )
        if user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password already set for this user",
            )

        # Update password and verify user
        try:
            await auth_service.update_password(user.id, user_register.password)
            await auth_service.verify_user(user.id)
            return {"is_success": True}
        except EntityUpdateError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user",
            )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_register.id}' not found",
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read user",
        )


@router.post(
    "/signin",
    responses={
        200: {"description": "User signin successful"},
        400: {
            "description": "Invalid credentials, user not verified, password not set, "
            "failed to create session, or failed to retrieve CSRF token"
        },
    },
)
async def signin(
    user_login: UserLogin,
    response: Response,
    auth_service: AuthServiceDependency,
    sessions_service: SessionsServiceDependency,
):
    """
    Sign in a user and create a session.

    - **user_login**: The login data containing user credentials.

    Raises:
    - **HTTPException**:
        - 400: If the credentials are invalid, user is not verified, password not set, failed to create session,
        or failed to retrieve CSRF token.

    Returns:
    - **dict**: A dictionary indicating success of the operation.
    """
    try:
        # Retrieve user data based on email
        user = await auth_service.read_auth_data(email=user_login.email)

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is not verified",
            )
        if not user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password not set for this user",
            )

        # Validate password
        is_valid_password = verify_password(user_login.password, user.password)
        if not is_valid_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
            )

        # Create session for the user
        try:
            session_id = await sessions_service.create_session(
                user.id, settings.SESSION_EXPIRE_TIME
            )
        except EntityCreateError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create session",
            )

        try:
            csrf_token = await sessions_service.get_csrf_token(session_id)
        except (EntityNotFoundError, EntityReadError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve CSRF token",
            )

        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_id,
            max_age=settings.SESSION_EXPIRE_TIME,
            httponly=True,
            samesite="lax",
            secure=not settings.DEBUG,
        )

        response.set_cookie(
            key=settings.CSRF_COOKIE_NAME,
            value=csrf_token,
            max_age=settings.CSRF_EXPIRE_TIME,
            httponly=False,  # Accessible by JavaScript
            samesite="lax",
            secure=not settings.DEBUG,
        )

        return {"is_success": True}

    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )
    except EntityReadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read user",
        )


@router.post(
    "/logout",
    responses={
        200: {"description": "User logged out successfully"},
        400: {"description": "No session found or failed to log out"},
    },
)
async def logout(
    response: Response,
    request: Request,
    sessions_service: SessionsServiceDependency,
):
    """
    Log out a user by deleting their session.

    Raises:
    - **HTTPException**:
        - 400: If no session found or failed to log out.

    Returns:
    - **dict**: A dictionary indicating success of the logout operation.
    """
    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No session found"
        )

    try:
        # Delete the session from the service
        await sessions_service.delete_session(session_id)
    # Session already does not exist
    except EntityNotFoundError:
        pass
    except EntityDeletionError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to log out",
        )

    # Remove the session cookie from the response
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    # Remove the CSRF token cookie from the response
    response.delete_cookie(settings.CSRF_COOKIE_NAME)
    return {"is_success": True}
