from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TagOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class DocumentVersionOut(BaseModel):
    id: int
    version_number: int
    file_size: int
    uploaded_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    title: str
    original_filename: str
    file_type: str
    summary: Optional[str] = None
    project_id: Optional[int] = None
    owner_id: int
    current_version: int
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagOut] = []

    class Config:
        from_attributes = True


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    project_id: Optional[int] = None


class DocumentListResponse(BaseModel):
    items: List[DocumentOut]
    total: int
    page: int
    page_size: int
    total_pages: int
