from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from presentation import dependencies as deps
from presentation.schemas import UserIn, UserResponse, TokenResponse
from application.common.utils import format_datetime_to_str

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserIn, user_service=Depends(deps.get_user_service)):
    created = await user_service.register_user(user.email, user.password)
    if created is None:
        raise HTTPException(status_code=400, detail="The user with provided e-mail already exists")
    return {"id": created.id, "email": created.email, "created_at": format_datetime_to_str(created.created_at)}


@router.post("/token", response_model=TokenResponse)
async def token(user: UserIn, user_service=Depends(deps.get_user_service)):
    token_info = await user_service.authenticate_user(user.email, user.password)
    if token_info is None:
        raise HTTPException(status_code=401, detail="Provided incorrect credentials")
    # token_info contains datetime for expires; convert to ISO
    return {"token_type": token_info["token_type"], "user_token": token_info["user_token"], "expires": token_info["expires"].isoformat()}
