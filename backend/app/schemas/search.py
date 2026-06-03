from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class SearchResultItem(BaseModel):
    id: int
    title: str
    file_type: str
    title_highlight: str
    summary_highlight: str
    content_highlight: str
    relevance: float
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    items: List[SearchResultItem]
    query: str
    total: int
    page: int
    page_size: int
