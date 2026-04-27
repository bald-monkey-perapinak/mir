from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_deps import validate_telegram_init_data, create_jwt, get_or_create_user
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

class TelegramAuthRequest(BaseModel):
    init_data: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str
    full_name: str | None

@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(body: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
                                                    
    telegram_user = validate_telegram_init_data(body.init_data)
    user = await get_or_create_user(telegram_user, db)

    token = create_jwt(user.id, user.telegram_id, user.role)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
    )
