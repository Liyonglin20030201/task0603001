from pydantic import BaseModel
from typing import List, Optional


class DiffLineOut(BaseModel):
    type: str
    line_left: Optional[int] = None
    line_right: Optional[int] = None
    content_left: str
    content_right: str


class DiffStats(BaseModel):
    additions: int
    deletions: int
    changes: int
    total_lines: int


class VersionDiffResponse(BaseModel):
    document_id: int
    version_left: int
    version_right: int
    diff_lines: List[DiffLineOut]
    stats: DiffStats
