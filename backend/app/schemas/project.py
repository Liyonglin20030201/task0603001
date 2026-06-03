from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ProjectMemberCreate(BaseModel):
    user_id: int
    role: str = "member"


class ProjectMemberOut(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    owner_id: Optional[int] = None
    created_at: datetime
    members: List[ProjectMemberOut] = []

    class Config:
        from_attributes = True
