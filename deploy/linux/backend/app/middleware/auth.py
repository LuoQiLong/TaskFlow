from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..utils.security import decode_access_token

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT token, return the authenticated user."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        # Reject tokens meant for other purposes (e.g. password_reset)
        if payload.get("type") is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been disabled",
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


def resolve_target_user(current_user: User, target_user_id: int | None) -> int | None:
    """Resolve effective user_id for admin scope switching.

    Returns:
        int  = view this specific user's data
        None = view ALL users' data (admin only, target_user_id == -1)
    Raises 403 if non-admin tries to view another user's data.
    """
    if target_user_id is None:
        return current_user.id  # default: self

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能查看其他用户数据",
        )

    if target_user_id == -1:
        return None  # view all
    return target_user_id
