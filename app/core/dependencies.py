from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from app.core.session import get_db
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from jose import JWTError, jwt

from app.models.user import User
from app.services.user_service import get_user_by_email
from app.core.token_blacklist import is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token: Optional[str] = None

    auth_header: Optional[str] = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        cookie_token: Optional[str] = request.cookies.get("access_token")
        if cookie_token:
            token = cookie_token.replace("Bearer ", "").strip()  

    if not token:
        print("No token found in request")
        raise credentials_exception

    if is_token_blacklisted(token):
        print(f"Token blacklisted: {token}")  
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email: Optional[str] = payload.get("sub")
        if not user_email:
            print("No 'sub' field in payload")
            raise credentials_exception

        user = await get_user_by_email(db, email=user_email)
        if not user or user.deleted:
            print(f"User not found or deleted: {user_email}")
            raise credentials_exception

    except JWTError as e:
        print(f"JWTError: {e}")
        raise credentials_exception

    return user