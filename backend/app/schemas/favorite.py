from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.document import DocumentOut


class FavoriteCategoryCreate(BaseModel):
    name: str


class FavoriteCategoryUpdate(BaseModel):
    name: str


class FavoriteCategoryOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    count: int = 0

    class Config:
        from_attributes = True


class FavoriteCreate(BaseModel):
    document_id: int
    category_id: Optional[int] = None


class FavoriteMoveCategory(BaseModel):
    category_id: Optional[int] = None


class FavoriteOut(BaseModel):
    id: int
    document_id: int
    category_id: Optional[int] = None
    created_at: datetime
    document: DocumentOut

    class Config:
        from_attributes = True


class FavoriteStatusOut(BaseModel):
    is_favorited: bool
    favorite_id: Optional[int] = None
    category_id: Optional[int] = None


class QuickAccessResponse(BaseModel):
    recent: List[DocumentOut]
    favorites: List[DocumentOut]
