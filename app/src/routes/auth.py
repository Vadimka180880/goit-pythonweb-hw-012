"""
Routes for authentication, registration, email verification, password reset, and user profile management.
"""

from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from jwt.exceptions import PyJWTError as JWTError
import logging
from app.src.schemas.users import UserResponse, UserCreate, UserEmailSchema, ResetPasswordSchema, RefreshTokenRequest
from app.src.services.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    reset_user_password,
    create_refresh_token,
    store_refresh_token,
    revoke_refresh_token,
    is_refresh_token_active
)
from app.src.repository.users import get_user_by_email, update_user_avatar, get_user_by_id
from app.src.services.email import send_verification_email, send_password_reset_email, create_password_reset_token
from app.src.services.cloudinary_service import upload_avatar
from app.src.config.config import settings
from app.src.database.models import User
from sqlalchemy.orm import Session 
from app.src.database.redis import get_redis
from app.src.database.base import get_db
from jose import jwt as jose_jwt

router = APIRouter(tags=["auth"])  
logger = logging.getLogger(__name__)

# AUTHENTICATION & REGISTRATION ENDPOINTS

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with the provided email and password. Sends a verification email to confirm the account."
)
async def signup(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    from app.src.repository.users import create_user
    from sqlalchemy.exc import IntegrityError
    try:
        user = await create_user(user_data, db)
        background_tasks.add_task(
            send_verification_email,
            email=user.email,
            user_id=user.id
        )
        return UserResponse.from_orm(user)
    except IntegrityError:
        await db.rollback()
        logger.error("SIGNUP IntegrityError: Duplicate email", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists."
        )
    except Exception as e:
        logger.error(f"SIGNUP EXCEPTION: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user due to an internal server error."
        )

@router.post(
    "/login",
    response_model=dict,
    summary="Authenticate a user",
    description="Authenticates a user with email and password, returning JWT access token and user details."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:        
        user = await get_user_by_email(form_data.username, db)
        if not user or not verify_password(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=15)
        )
        refresh_token = create_refresh_token({"sub": user.email})
        # Store refresh token in Redis
        payload = jose_jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        await store_refresh_token(payload["jti"], user.email)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LOGIN EXCEPTION: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# EMAIL VERIFICATION ENDPOINT

@router.get("/verify/{verification_code}")
async def verify_email_endpoint(verification_code: str, db: Session = Depends(get_db)):
    """
    Confirms the user's email by the verification code.

    Args:
        verification_code (str): The verification code received in the email.
        db (Session): Database session.

    Returns:
        dict: Message about the verification result.

    Raises:
        HTTPException: If the code is invalid or an error occurred.
    """
    return await verify_email(verification_code, db)

@router.get(
    "/verify-email",
    summary="Verify email",
    description="Verifies a user's email using the provided verification token sent to their email."
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirms email by JWT token.

    Args:
        token (str): Verification token.
        db (AsyncSession): Async database session.

    Returns:
        dict: Result message.

    Raises:
        HTTPException: If the token is invalid, expired, or an error occurred.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "email_verification":
            logger.error(f"Invalid token payload: {payload}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )

        user = await get_user_by_id(int(user_id), db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.confirmed:
            return {"message": "Email already verified"}

        user.confirmed = True
        await db.commit()

        return {"message": "Email successfully verified"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )

# USER PROFILE ENDPOINTS

@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    summary="Get current user profile",
    description="Retrieves the profile information of the currently authenticated user."
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the profile of the currently authenticated user.

    Args:
        current_user (User): The current user object.

    Returns:
        UserResponse: Profile data.

    Raises:
        HTTPException: If access is restricted.
    """
    return UserResponse.from_orm(current_user)

# AVATAR MANAGEMENT ENDPOINT

@router.patch(
    "/avatar",
    response_model=UserResponse,
    summary="Update user avatar",
    description="Uploads a new avatar for the authenticated user."
)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the user's avatar.

    Args:
        file (UploadFile): Uploaded avatar file.
        current_user (User): Current user.
        db (AsyncSession): Async database session.

    Returns:
        UserResponse: Updated user data.

    Raises:
        HTTPException: If the update failed.
    """
    try:
        avatar_url = await upload_avatar(file, current_user.email)
        updated_user = await update_user_avatar(current_user.id, avatar_url, db)
        return UserResponse.from_orm(updated_user)
    except Exception as e:
        logger.error(f"Update avatar error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update avatar"
        )

# PASSWORD RESET ENDPOINTS

@router.post(
    "/password-reset-request",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Sends a password reset email."
)
async def request_password_reset(
    user_email: UserEmailSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Requests a password reset.

    Args:
        user_email (UserEmailSchema): Email for password reset.
        background_tasks (BackgroundTasks): Tasks for sending email.
        db (AsyncSession): Async database session.

    Returns:
        dict: Message about sending.

    Raises:
        HTTPException: If an error occurred.
    """
    try:
        user = await get_user_by_email(user_email.email, db)
        if not user:
            return {"message": "If the email exists, password reset instructions have been sent"}

        reset_token = create_password_reset_token(user_email.email)
        background_tasks.add_task(
            send_password_reset_email,
            email=user_email.email,
            reset_token=reset_token
        )

        return {"message": "Password reset instructions have been sent"}
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset"
        )

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Resets the user's password."
)
async def reset_password(
    reset_data: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Resets the user's password.

    Args:
        reset_data (ResetPasswordSchema): Token and new password.
        db (AsyncSession): Async database session.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If the token is invalid or an error occurred.
    """
    try:
        if not reset_data.token or not reset_data.new_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Token and new password are required"
            )

        user = await reset_user_password(reset_data.token, reset_data.new_password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )

        return {"message": "Password has been reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

# TOKEN REFRESH ENDPOINT

@router.post(
    "/refresh-token",
    response_model=dict,
    summary="Refresh JWT tokens",
    description="Returns new access and refresh tokens using a valid refresh token."
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refreshes JWT tokens using a valid refresh token with rotation and revocation.
    """
    from app.src.services.auth import get_current_user_from_refresh, create_access_token, create_refresh_token
    try:
        token = request.token
        payload = jose_jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
        jti = payload.get("jti")
        email = payload.get("sub")
        if not jti or not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        # Check if token is active
        if not await is_refresh_token_active(jti):
            raise HTTPException(status_code=401, detail="Refresh token revoked or expired")
        # Revoke old token
        await revoke_refresh_token(jti)
        # Issue new tokens
        access_token = create_access_token({"sub": email}, expires_delta=timedelta(minutes=15))
        new_refresh_token = create_refresh_token({"sub": email})
        new_payload = jose_jwt.decode(new_refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        await store_refresh_token(new_payload["jti"], email)
        return {"access_token": access_token, "refresh_token": new_refresh_token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")