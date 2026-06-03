from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class DocumentAccess(Base):
    __tablename__ = "document_accesses"
    __table_args__ = (UniqueConstraint("user_id", "document_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    accessed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    document = relationship("Document")
