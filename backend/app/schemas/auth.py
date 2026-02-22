from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str  # ISO format string


class AuthResponse(BaseModel):
    user: UserResponse
    token: str


class ErrorResponse(BaseModel):
    error: str
    message: str
