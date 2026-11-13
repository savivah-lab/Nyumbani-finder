from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.phone_number == body.phone_number)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this phone number already exists")
    user = User(phone_number=body.phone_number, full_name=body.full_name.strip(),
                password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_access_token(user.id, user.role.value), user=user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.phone_number == body.phone_number))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect phone number or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been disabled")
    return TokenOut(access_token=create_access_token(user.id, user.role.value), user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
