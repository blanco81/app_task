from nanoid import generate
from sqlalchemy import Column, Index, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType
from app.config import settings
from app.core.base import Base
from app.utils.mixins import SoftDeleteMixin, TimestampMixin

KEY = settings.DB_SECRET_KEY

class Task(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(String(40), primary_key=True, default=generate)
    task_name = Column(StringEncryptedType(String(200), KEY), index=True)
    description = Column(StringEncryptedType(Text, KEY), nullable=True)
    status = Column(StringEncryptedType(String(200), KEY), default="pending", nullable=False)
    
    user_id = Column(String(40), ForeignKey(f"users.id"))
    user = relationship("User", back_populates="tasks", lazy="selectin")
    
    __table_args__ = (
        Index("ix_tasks_user_id", "user_id"),
        Index("ix_tasks_created_at", "created_at"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_deleted", "deleted"),
    )
    
    