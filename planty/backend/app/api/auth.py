from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import create_token, hash_password, verify_password
from app.models.database import get_db
from app.models.entities import User
from app.models.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    access = create_token(user.email, 60, "access")
    refresh = create_token(user.email, 60 * 24 * 7, "refresh")
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Bad credentials")
    return TokenPair(
        access_token=create_token(user.email, 60, "access"),
        refresh_token=create_token(user.email, 60 * 24 * 7, "refresh"),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest):
    from app.auth.security import decode_token

    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token")
    subject = data["sub"]
    return TokenPair(
        access_token=create_token(subject, 60, "access"),
        refresh_token=create_token(subject, 60 * 24 * 7, "refresh"),
    )


@router.post("/logout")
def logout():
    return {"status": "ok"}
