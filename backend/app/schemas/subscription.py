from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class SubscriptionCreate(BaseModel):
    document_id: Optional[int] = None
    project_id: Optional[int] = None


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    document_id: Optional[int]
    project_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    event_type: str
    document_id: Optional[int]
    actor_id: Optional[int]
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationOut]
    total: int
    unread_count: int
