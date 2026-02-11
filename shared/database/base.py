import uuid
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):

    @declared_attr.directive
    def __tablename__(cls):
        return cls.__name__.lower()


class TimestampMixin:
    created_at = DateTime(timezone=True)
    updated_at = DateTime(timezone=True)
