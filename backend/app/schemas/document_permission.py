from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentPermissionCreate(BaseModel):
    user_id: int
    permission_level: str


class DocumentPermissionOut(BaseModel):
    id: int
    document_id: int
    user_id: int
    permission_level: str
    granted_at: datetime
    granted_by: Optional[int] = None

    class Config:
        from_attributes = True
