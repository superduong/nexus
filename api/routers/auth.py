from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.core.deps import decode_refresh_token, get_current_user
from api.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from api.db.models import ExchangeAPIKey, User
from api.db.session import get_db
from api.schemas.auth import (
    ExchangeKeyCreate,
    ExchangeKeyOut,
    LoginIn,
    RefreshIn,
    RegisterIn,
    TokenPair,
    UserOut,
    UserUpdate,
)

router = APIRouter()


def _tokens_for_user(user: User) -> TokenPair:
    claims = {"sub": str(user.id), "email": user.email, "username": user.username}
    return TokenPair(access=create_access_token(claims), refresh=create_refresh_token(claims))


@router.post("/login/", response_model=TokenPair)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _tokens_for_user(user)


@router.post("/refresh/", response_model=TokenPair)
def refresh_token(body: RefreshIn, db: Session = Depends(get_db)):
    payload = decode_refresh_token(body.refresh)
    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return _tokens_for_user(user)


@router.post("/register/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    user = User(
        email=body.email,
        username=body.username,
        first_name="",
        last_name="",
        password=hash_password(body.password),
        date_joined=now,
        created_at=now,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already exists")
    db.refresh(user)
    return user


@router.get("/me/", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me/", response_model=UserOut)
def patch_me(body: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.get("/keys/", response_model=list[ExchangeKeyOut])
def list_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(ExchangeAPIKey).where(ExchangeAPIKey.user_id == user.id)).all()
    return rows


@router.post("/keys/", response_model=ExchangeKeyOut, status_code=status.HTTP_201_CREATED)
def create_key(body: ExchangeKeyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = ExchangeAPIKey(
        user_id=user.id,
        exchange=body.exchange,
        label=body.label,
        api_key=body.api_key,
        api_secret=body.api_secret,
        api_password=body.api_password,
        is_active=body.is_active,
        testnet=body.testnet,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate key for this exchange/label")
    db.refresh(row)
    return row


@router.get("/keys/{pk}/", response_model=ExchangeKeyOut)
def get_key(pk: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(ExchangeAPIKey, pk)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return row


@router.patch("/keys/{pk}/", response_model=ExchangeKeyOut)
def patch_key(
    pk: int, body: ExchangeKeyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    row = db.get(ExchangeAPIKey, pk)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    row.exchange = body.exchange
    row.label = body.label
    row.api_key = body.api_key
    row.api_secret = body.api_secret
    row.api_password = body.api_password
    row.is_active = body.is_active
    row.testnet = body.testnet
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate key for this exchange/label")
    db.refresh(row)
    return row


@router.delete("/keys/{pk}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_key(pk: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(ExchangeAPIKey, pk)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(row)
    db.commit()
