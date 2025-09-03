from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import settings
from app.models.user import Log, User
from app.schemas.user_schema import LogOut, PaginatedLogsResponse, PaginatedUsers, UserResponse, UserUpdate
from app.services.user_service import (
    get_user, 
    get_users, 
    update_user, 
    deactivate_user, 
    activate_user
)
from app.core.session import get_db
from app.core.dependencies import get_current_user

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Permiso denegado")
    return current_user


@router.get("", response_model=List[UserResponse])
async def read_users(
    limit: int = Query(default=settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):     
    users = await get_users(db, offset=offset, limit=limit)
    return [
        UserResponse(
            id=user.id,
            name_complete=user.name_complete,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ) for user in users
    ]

@router.get("/filter", response_model=PaginatedUsers, tags=["Usuarios"])
async def filter_list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),  
    limit: int = Query(default=settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
):
    try:
        stmt = select(User).where(User.deleted == False).order_by(User.created_at.desc())
        result = await db.execute(stmt)
        users = result.scalars().all()

        users_dict = [{
            "id": str(user.id),
            "name_complete": user.name_complete,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        } for user in users]

        if search:
            search_term = search.lower().strip()
            filtered_users = []

            for user in users_dict:
                score = 0
                name_complete = user["name_complete"].lower()
                email = user["email"].lower()
                role = user["role"].lower()

                if name_complete.startswith(search_term):
                    score += 100
                elif search_term in name_complete:
                    score += 30

                if email.startswith(search_term) or role.startswith(search_term):
                    score += 50
                elif search_term in email or search_term in role:
                    score += 20

                if score > 0:
                    user["score"] = score
                    filtered_users.append(user)

            filtered_users.sort(key=lambda x: (-x["score"], x["name_complete"]))
            users_dict = filtered_users

        total_users = len(users_dict)
        paginated_users = users_dict[offset: offset + limit]

        return {
            "total": total_users,
            "users": paginated_users,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}")
    
@router.get("/logs", response_model=PaginatedLogsResponse)
async def list_logs_paginated(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    limit: int = Query(default=settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):    
    
    try:
        # Query para los logs (sin joinedload ya que el schema solo necesita user_id)
        query = (
            select(Log)
            .order_by(Log.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        # Query para el conteo total
        count_query = select(func.count()).select_from(Log)
        
        # Ejecutar queries
        result = await db.execute(query)
        logs = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Crear respuesta usando el schema LogOut
        logs_response = [
            LogOut(
                id=log.id,
                action=log.action,
                created_at=log.created_at,
                user_id=str(log.user_id) if log.user_id is not None else ""  # Manejar None
            )
            for log in logs
        ]

        return PaginatedLogsResponse(
            total=total,
            limit=limit,
            offset=offset,
            logs=logs_response
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener logs: {str(e)}")
    
@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return UserResponse(
        id=user.id,
        name_complete=user.name_complete,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def edit_user(
    user_id: str,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = await update_user(db, user_id, user)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return UserResponse(
        id=user.id,
        name_complete=user.name_complete,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def deactivate_user_route(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user_deleted = await deactivate_user(db, user_id)
    if not user_deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"desactivado": "ok"}


@router.post("/activate/{user_id}", status_code=status.HTTP_200_OK)
async def activate_user_route(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user_activated = await activate_user(db, user_id)
    if not user_activated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"activado": "ok"}






