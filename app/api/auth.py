from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.user import User
from app.schemas.user_schema import AccessToken, LoginRequest, UserCreate, UserResponse
from app.services.user_service import get_user_by_email, create_user
from app.core.session import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.core.token_blacklist import add_token_to_blacklist

router = APIRouter()


@router.post("/login", response_model=AccessToken)
async def login(
    response: Response,  
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    db_user = await get_user_by_email(db, login_data.email)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no existe")
    if db_user.deleted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario no habilitado")
    if not login_data.password == db_user.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    access_token = create_access_token(data={"sub": db_user.email, "role": str(db_user.role)})
    
    response.set_cookie(
        key="access_token", 
        value=access_token,  
        httponly=True, 
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,  
        samesite="lax",
    )

    return AccessToken(access_token=access_token, token_type="Bearer")
    

@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db),
    response: Response = None  
):
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        response = JSONResponse(
            status_code=400,
            content={"detail": "Este email ya está registrado."}
        )
        response.delete_cookie(key="access_token")  # Limpiar por si acaso
        return response
    
    new_user = await create_user(db, user)
    if not new_user:
        raise HTTPException(status_code=500, detail="Error al crear usuario")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email, "role": str(new_user.role)},
        expires_delta=access_token_expires
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token, 
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )
    
    return new_user
    

@router.get("/me", response_model=UserResponse)
async def get_current_user_data(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
    ):
    try:
        return UserResponse(
            id=current_user.id,
            name_complete=current_user.name_complete,
            email=current_user.email,
            role=current_user.role,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
        )
    except Exception as e:
        print(f"Error fetching current user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.get("/logout")
async def logout(request: Request):
    response = JSONResponse(
        status_code=200,
        content={"message": "Sesión finalizada"}
    )

    token = request.cookies.get("access_token")
    
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1] if len(token.split(" ")) > 1 else token
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token_from_header = auth_header.split(" ")[1]
        
        if not token:
            token = token_from_header
        elif token != token_from_header:
            add_token_to_blacklist(token_from_header)

    if token:
        print(f"Adding to blacklist: {token}")  # Para depuración
        add_token_to_blacklist(token)

    response.delete_cookie(
        key="access_token",
        httponly=True,
        path="/",
        secure=False
    )
    return response
