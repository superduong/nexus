from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh: str


class TokenPair(BaseModel):
    access: str
    refresh: str


class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    created_at: datetime


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class ExchangeKeyCreate(BaseModel):
    exchange: str
    label: str = ""
    api_key: str
    api_secret: str
    api_password: str = ""
    is_active: bool = True
    testnet: bool = False


class ExchangeKeyOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    exchange: str
    label: str
    api_key: str
    api_password: str = ""
    is_active: bool
    testnet: bool
    created_at: datetime
