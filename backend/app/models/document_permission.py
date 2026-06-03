from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class DocumentPermission(Base):
    __tablename__ = "document_permissions"
    __table_args__ = (UniqueConstraint("document_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_level = Column(String(10), nullable=False)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    document = relationship("Document", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])
