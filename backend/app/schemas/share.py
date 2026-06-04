from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ShareLinkCreate(BaseModel):
    is_permanent: bool = False
    expires_at: Optional[datetime] = None
    max_access_count: Optional[int] = None
    password: Optional[str] = None


class ShareLinkOut(BaseModel):
    id: int
    document_id: int
    token: str
    is_permanent: bool
    expires_at: Optional[datetime]
    max_access_count: Optional[int]
    current_access_count: int
    has_password: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ShareAccessRequest(BaseModel):
    password: str


class SharedDocumentOut(BaseModel):
    id: int
    title: str
    original_filename: str
    file_type: str
    summary: Optional[str]
    content: Optional[str]
    current_version: int
    created_at: datetime

    class Config:
        from_attributes = True
