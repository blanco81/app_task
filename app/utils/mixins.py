from datetime import datetime
import pytz
from sqlalchemy import Column, Boolean, DateTime, select
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query

class SoftDeleteMixin:   
    @declared_attr
    def deleted(cls):       
        return Column(Boolean, default=False)

    @classmethod
    async def soft_delete(cls, db, id: str) -> bool:
        query = select(cls).where(cls.id == id, cls.deleted == False)
        result = await db.execute(query)
        instance = result.scalars().first()
        if instance:
            instance.deleted = True
            await db.commit()
            return True
        return False

    @classmethod
    def filter_deleted(cls, query: Query) -> Query:
        return query.filter(cls.deleted == False)    
    
class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(pytz.utc))
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))

class TimestampLogMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(pytz.utc))    
    