from __future__ import annotations

from fastapi import APIRouter

from .schemas import CreateUserRequest, UserResponse

router = APIRouter()


@router.post("/users", response_model=UserResponse)
async def create_user(user: CreateUserRequest) -> UserResponse:
    # In a real app, persist to DB here
    return UserResponse(**user.model_dump())
