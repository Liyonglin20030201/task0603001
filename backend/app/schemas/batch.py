from pydantic import BaseModel
from typing import List


class BatchDeleteRequest(BaseModel):
    document_ids: List[int]


class BatchMoveRequest(BaseModel):
    document_ids: List[int]
    project_id: int


class BatchTagRequest(BaseModel):
    document_ids: List[int]
    tag_names: List[str]


class BatchPermissionRequest(BaseModel):
    document_ids: List[int]
    user_id: int
    permission_level: str


class BatchErrorItem(BaseModel):
    document_id: int
    error: str


class BatchResultOut(BaseModel):
    total: int
    succeeded: int
    failed: int
    errors: List[BatchErrorItem] = []
