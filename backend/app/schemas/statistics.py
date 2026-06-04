from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class PopularDocumentOut(BaseModel):
    document_id: int
    title: str
    access_count: int


class ActiveUserOut(BaseModel):
    user_id: int
    username: str
    access_count: int


class SystemStatsOut(BaseModel):
    total_documents: int
    total_visits: int
    total_users: int
    popular_documents: List[PopularDocumentOut]
    active_users: List[ActiveUserOut]


class AccessRecordOut(BaseModel):
    user_id: int
    username: str
    accessed_at: datetime


class VersionHistoryOut(BaseModel):
    version_number: int
    uploaded_by: Optional[int]
    uploader_username: Optional[str]
    file_size: int
    created_at: datetime


class DocumentStatsOut(BaseModel):
    document_id: int
    total_accesses: int
    access_records: List[AccessRecordOut]
    version_history: List[VersionHistoryOut]
