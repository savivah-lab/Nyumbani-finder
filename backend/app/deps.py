import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Role, User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def _user_from_creds(creds: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account not found or disabled")
    return user


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    user = _user_from_creds(creds, db)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


def get_optional_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    return _user_from_creds(creds, db)


def require_role(*roles: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to do that")
        return user
    return checker
