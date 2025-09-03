from nanoid import generate
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType
from app.config import settings
from app.core.base import Base
from app.utils.mixins import SoftDeleteMixin, TimestampMixin, TimestampLogMixin

KEY = settings.DB_SECRET_KEY

class User(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(40), primary_key=True, default=generate)
    name_complete = Column(StringEncryptedType(String(200), KEY), nullable=False)  
    email = Column(StringEncryptedType(String(200), KEY), unique=True)  
    password = Column(StringEncryptedType(String(200), KEY), nullable=False)  
    role = Column(StringEncryptedType(String(200), KEY), nullable=False)  # Admin, Public
    
    logs = relationship("Log", back_populates="user", lazy="selectin")
    tasks = relationship("Task", back_populates="user", lazy="selectin")
    

class Log(Base, TimestampLogMixin):
    __tablename__ = "logs"

    id = Column(String(40), primary_key=True, default=generate)
    action = Column(StringEncryptedType(String(200), KEY), nullable=False)      
    user_id = Column(String(40), ForeignKey(f"users.id"))
    user = relationship("User", back_populates="logs", lazy="selectin")
