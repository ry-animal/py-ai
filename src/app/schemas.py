from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    is_active: bool = True


class UserResponse(BaseModel):
    username: str
    email: EmailStr
    is_active: bool


class ExtractUserRequest(BaseModel):
    text: str = Field(min_length=1, description="Freeform text that contains user info")


class ExtractedUser(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr


