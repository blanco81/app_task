from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import settings
from app.models.task import Task
from app.models.user import User
from app.schemas.task_schema import PaginatedTasks, TaskResponse, TaskCreate, TaskUpdate
from app.services.task_service import (
    get_task,
    get_tasks_by_user,
    create_task,
    update_task,
    deactivate_task,
)
from app.core.session import get_db
from app.core.dependencies import get_current_user

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Permiso denegado")
    return current_user


@router.get("", response_model=List[TaskResponse])
async def read_my_tasks(
    limit: int = Query(default=settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks, _ = await get_tasks_by_user(
        db, user_id=current_user.id, limit=limit, offset=offset
    )
    return [
        TaskResponse(
            id=task.id,
            task_name=task.task_name,
            description=task.description,
            status=task.status,
            user_id=task.user_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in tasks
    ]
    
@router.get("/filter", response_model=PaginatedTasks, tags=["Tareas"])
async def filter_list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
):
    try:
        
        stmt = select(Task).where(
            Task.deleted == False,
            Task.user_id == current_user.id  
        ).order_by(Task.created_at.desc())

        result = await db.execute(stmt)
        tasks = result.scalars().all()

        tasks_dict = [{
            "id": str(task.id),
            "task_name": task.task_name,
            "description": task.description,
            "status": task.status,
            "user_id": task.user_id,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        } for task in tasks]

        if search:
            search_term = search.lower().strip()
            filtered_tasks = []

            for task in tasks_dict:
                score = 0
                task_name = (task["task_name"] or "").lower()
                description = (task["description"] or "").lower()
                status = (task["status"] or "").lower()

                if task_name.startswith(search_term):
                    score += 100
                elif search_term in task_name:
                    score += 30

                if description and (description.startswith(search_term) or search_term in description):
                    score += 50

                if status.startswith(search_term) or search_term in status:
                    score += 20

                if score > 0:
                    task["score"] = score
                    filtered_tasks.append(task)

            filtered_tasks.sort(key=lambda x: (-x["score"], x["task_name"]))
            tasks_dict = filtered_tasks

        total_tasks = len(tasks_dict)
        paginated_tasks = tasks_dict[offset: offset + limit]

        return {
            "total": total_tasks,
            "tasks": paginated_tasks,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas: {str(e)}")


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task_route(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_task = await create_task(db, task, current_user.id)
    return TaskResponse.model_validate(new_task)


@router.get("/{task_id}", response_model=TaskResponse)
async def read_my_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):    
    task = await get_task(db, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_my_task(
    task_id: str,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_task = await get_task(db, task_id)
    if not db_task or db_task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    task_updated = await update_task(db, task_id, task, current_user.id)
    return TaskResponse.model_validate(task_updated)


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_my_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_task = await get_task(db, task_id)
    if not db_task or db_task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    await deactivate_task(db, task_id, current_user.id)
    return {"eliminada": "ok"}



