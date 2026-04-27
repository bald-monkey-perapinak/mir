import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

bearer = HTTPBearer(auto_error=False)

def validate_telegram_init_data(init_data: str) -> dict:
                                                                        
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=503, detail="BOT_TOKEN is not configured")
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", "")
        logger.info(f"Received init_data keys: {list(parsed.keys())}")

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256
        ).digest()

        expected_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            raise HTTPException(
                status_code=401, detail="Invalid Telegram auth data")

                            
        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            raise HTTPException(status_code=401, detail="Auth data expired")

        user_data = json.loads(parsed.get("user", "{}"))
        return user_data

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        logger.exception("Telegram auth validation error")
        raise HTTPException(
            status_code=401, detail=f"Invalid init data: {str(e)}")

def create_jwt(user_id: str, telegram_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "telegram_id": telegram_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_jwt(credentials.credentials)
    user_id = payload.get("sub")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401, detail="User not found or inactive")

    return user

async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def get_or_create_user(telegram_user: dict, db: AsyncSession) -> User:
    telegram_id = telegram_user["id"]
    admin_ids = settings.get_admin_ids()
    role = "admin" if telegram_id in admin_ids else "doctor"

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        user.last_login_at = datetime.now(timezone.utc)
        user.role = role                                          
        await db.commit()
        return user

    user = User(
        telegram_id=telegram_id,
        username=telegram_user.get("username"),
        full_name=f"{telegram_user.get('first_name', '')} {telegram_user.get('last_name', '')}".strip(
        ),
        role=role,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
