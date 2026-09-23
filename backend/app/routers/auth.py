from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.security import verify_password, create_access_token, create_refresh_token
from ..core.dependencies import get_current_user
from ..models.user import User
from ..schemas.auth import LoginRequest, TokenResponse, UserOut
from ..schemas.common import ApiResponse
from ..core.config import settings

router = APIRouter()


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(
        subject=user.user_id,
        extra={"role": user.role, "name": user.name, "operator_id": user.operator_id},
    )
    refresh_token = create_refresh_token(subject=user.user_id)

    return ApiResponse(data=TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserOut.model_validate(user),
    ))


@router.get("/me", response_model=ApiResponse[UserOut])
async def get_me(current_user=Depends(get_current_user)):
    return ApiResponse(data=UserOut.model_validate(current_user))
