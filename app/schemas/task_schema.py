from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TaskCreate(BaseModel):
    task_name: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    task_name: str
    description: Optional[str]
    status: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedTasks(BaseModel):
    total: int
    limit: int
    offset: int
    tasks: List[TaskResponse]
