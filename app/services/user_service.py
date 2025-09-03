from datetime import datetime
import pytz
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from app.config import settings
from app.models.user import User, Log
from app.schemas.user_schema import PaginatedUsers, UserCreate, UserResponse, UserUpdate


async def get_user(db: AsyncSession, user_id: str) -> User:    
    result = await db.execute(select(User).where(User.id == user_id, User.deleted == False))
    usuario = result.scalars().first()      
    return usuario

async def get_user_by_email(db: AsyncSession, email: str) -> User:
    result = await db.execute(select(User).where(User.email == email, User.deleted == False))
    usuario = result.scalars().first()        
    return usuario

async def get_users(
    db: AsyncSession,
    offset: int = 0,
    limit: int = settings.DEFAULT_LIMIT
) -> List[User]:
    query = (
        select(User)
        .where(User.deleted.is_(False))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().unique().all()

async def get_users_by_role(db: AsyncSession) -> List[User]:
    query = (
    select(User)
    .where(        
        User.role.in_(["Admin", "Public"]),
        User.deleted.is_(False)
    )
)
    result = await db.execute(query)        
    usuarios = result.scalars().all()  
    return usuarios  

async def get_user_deactivate(db: AsyncSession, user_id: str) -> User:    
    result = await db.execute(select(User).where(User.id == user_id, User.deleted == True))
    usuario = result.scalars().first()      
    return usuario

async def create_user(db: AsyncSession, usuario: UserCreate) -> User:
    user_data = usuario.dict(exclude_unset=True)
    usuario = User(**user_data)

    db.add(usuario)

    db_log = Log(
        action=f"Usuario '{usuario.name_complete}' fue creado.",
        created_at=datetime.now(pytz.utc),
        user_id=usuario.id
    )
    db.add(db_log)

    await db.commit()
    await db.refresh(usuario)
    await db.refresh(db_log)

    return usuario

async def update_user(db: AsyncSession, user_id: str, usuario_data: UserUpdate) -> Optional[User]:
    usuario = await get_user(db, user_id)
    if not usuario:
        return None

    for field, value in usuario_data.dict(exclude_unset=True).items():
        setattr(usuario, field, value)

    db_log = Log(
        action=f"Usuario '{usuario.name_complete}' fue actualizado.",
        created_at=datetime.now(pytz.utc),
        user_id=usuario.id
    )
    db.add(db_log)

    await db.commit()
    await db.refresh(usuario)
    await db.refresh(db_log)

    return usuario

async def deactivate_user(db: AsyncSession, user_id: str) -> bool:
    usuario = await get_user(db, user_id)
    if not usuario:
        return False

    usuario.deleted = True

    db_log = Log(
        action=f"Usuario '{usuario.name_complete}' fue deshabilitado.",
        created_at=datetime.now(pytz.utc),
        user_id=usuario.id
    )
    db.add(db_log)

    await db.commit()
    await db.refresh(usuario)
    await db.refresh(db_log)

    return True


async def activate_user(db: AsyncSession, user_id: str) -> bool:
    usuario = await get_user_deactivate(db, user_id)
    if not usuario:
        return False

    usuario.deleted = False

    db_log = Log(
        action=f"Usuario '{usuario.name_complete}' fue habilitado.",
        created_at=datetime.now(pytz.utc),
        user_id=usuario.id
    )
    db.add(db_log)

    await db.commit()
    await db.refresh(usuario)
    await db.refresh(db_log)

    return True



