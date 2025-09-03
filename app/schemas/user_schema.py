from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    name_complete: str
    email: EmailStr
    role: str

class UserCreate(UserBase):   
    password: str 

class UserUpdate(BaseModel):
    name_complete: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedUsers(BaseModel):
    total: int
    limit: int
    offset: int
    users: List[UserResponse]
    
class LogOut(BaseModel):
    id: str
    action: str
    created_at: datetime
    user_id: str

    class Config:
        from_attributes = True

class PaginatedLogsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    logs: List[LogOut]

    class Config:
        from_attributes = True
