from datetime import datetime
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional, Dict, Any, Tuple
from app.config import settings
from app.models.task import Task
from app.models.user import Log
from app.schemas.task_schema import TaskCreate, TaskUpdate


async def get_task(db: AsyncSession, task_id: str) -> Optional[Task]:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.deleted.is_(False))
    )
    return result.scalars().first()


async def get_tasks(
    db: AsyncSession,
    offset: int = 0,
    limit: int = settings.DEFAULT_LIMIT
) -> List[Task]:
    query = (
        select(Task)
        .where(Task.deleted.is_(False))
        .order_by(Task.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().unique().all()


async def get_tasks_by_user(
    db: AsyncSession, 
    user_id: str, 
    limit: int = settings.DEFAULT_LIMIT,
    offset: int = 0
) -> Tuple[List[Task], int]:
    total_query = select(func.count(Task.id)).where(
        Task.user_id == user_id, Task.deleted.is_(False)
    )
    total = (await db.execute(total_query)).scalar_one()

    query = (
        select(Task)
        .where(Task.user_id == user_id, Task.deleted.is_(False))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    tasks = result.scalars().unique().all()

    return tasks, total


async def create_task(db: AsyncSession, task: TaskCreate, user_id: str) -> Task:
    task_data = task.dict(exclude_unset=True)
    tarea = Task(**task_data, user_id=user_id)

    db.add(tarea)
    db.add(Log(
        action=f"Tarea '{tarea.task_name}' fue creada.",
        created_at=datetime.now(pytz.utc),
        user_id=user_id
    ))

    await db.commit()
    await db.refresh(tarea)
    return tarea


async def update_task(db: AsyncSession, task_id: str, task_data: TaskUpdate, user_id: str) -> Optional[Task]:
    tarea = await get_task(db, task_id)
    if not tarea:
        return None

    for field, value in task_data.dict(exclude_unset=True).items():
        setattr(tarea, field, value)

    db.add(Log(
        action=f"Tarea '{tarea.task_name}' fue actualizada.",
        created_at=datetime.now(pytz.utc),
        user_id=user_id
    ))

    await db.commit()
    await db.refresh(tarea)
    return tarea


async def deactivate_task(db: AsyncSession, task_id: str, user_id: str) -> bool:
    tarea = await get_task(db, task_id)
    if not tarea:
        return False

    tarea.deleted = True
    db.add(Log(
        action=f"Tarea '{tarea.task_name}' fue deshabilitada.",
        created_at=datetime.now(pytz.utc),
        user_id=user_id
    ))

    await db.commit()
    await db.refresh(tarea)
    return True

async def activate_task(db: AsyncSession, task_id: str, user_id: str) -> bool:
    tarea = await get_task(db, task_id)
    if not tarea or tarea.deleted is False:  
        return False
    
    tarea.deleted = False

    db_log = Log(
        action=f"Tarea '{tarea.task_name}' fue habilitada.",
        created_at=datetime.now(pytz.utc),
        user_id=user_id
    )
    db.add(db_log)

    await db.commit()
    await db.refresh(tarea)
    await db.refresh(db_log)

    return True

