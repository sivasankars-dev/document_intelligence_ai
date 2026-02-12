from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from shared.database.base import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True)
    document_id = Column(ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())
