"""
FastAPI dependency helpers — auth, RBAC, DB session.
"""
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from .database import get_db
from .security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)

# Role hierarchy (higher index = more permissions)
ROLE_HIERARCHY = [
    "operator",
    "maintenance_engineer",
    "safety_officer",
    "supervisor",
    "engineer",
    "admin",
]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Extract and validate JWT, return user dict."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Import here to avoid circular imports
    from ..models.user import User
    from sqlalchemy import select

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.user_id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(allowed_roles: list[str]):
    """
    Returns a dependency that enforces role-based access.
    Usage: Depends(require_role(["engineer", "admin"]))
    """
    async def check(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' does not have access. Required: {allowed_roles}",
            )
        return current_user
    return check


def require_min_role(min_role: str):
    """Require at least this role level (by hierarchy)."""
    min_idx = ROLE_HIERARCHY.index(min_role) if min_role in ROLE_HIERARCHY else 0

    async def check(current_user=Depends(get_current_user)):
        user_idx = ROLE_HIERARCHY.index(current_user.role) if current_user.role in ROLE_HIERARCHY else -1
        if user_idx < min_idx:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Minimum role required: {min_role}",
            )
        return current_user
    return check


class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=50, ge=1, le=200),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
