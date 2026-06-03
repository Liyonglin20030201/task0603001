from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.favorite import Favorite, FavoriteCategory
from app.models.document_access import DocumentAccess
from app.schemas.favorite import (
    FavoriteCreate, FavoriteOut, FavoriteStatusOut, FavoriteMoveCategory,
    FavoriteCategoryCreate, FavoriteCategoryUpdate, FavoriteCategoryOut,
    QuickAccessResponse,
)
from app.schemas.document import DocumentOut

router = APIRouter()


@router.get("/quick-access", response_model=QuickAccessResponse)
def get_quick_access(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recent_accesses = (
        db.query(DocumentAccess)
        .filter(DocumentAccess.user_id == current_user.id)
        .order_by(DocumentAccess.accessed_at.desc())
        .limit(10)
        .all()
    )
    recent_docs = []
    for access in recent_accesses:
        doc = db.query(Document).filter(
            Document.id == access.document_id, Document.is_deleted == False
        ).first()
        if doc:
            recent_docs.append(doc)

    fav_records = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .limit(10)
        .all()
    )
    fav_docs = []
    for fav in fav_records:
        doc = db.query(Document).filter(
            Document.id == fav.document_id, Document.is_deleted == False
        ).first()
        if doc:
            fav_docs.append(doc)

    return QuickAccessResponse(recent=recent_docs, favorites=fav_docs)


@router.get("/categories", response_model=list[FavoriteCategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    categories = (
        db.query(FavoriteCategory)
        .filter(FavoriteCategory.user_id == current_user.id)
        .order_by(FavoriteCategory.created_at)
        .all()
    )
    result = []
    for cat in categories:
        count = db.query(func.count(Favorite.id)).filter(
            Favorite.category_id == cat.id
        ).scalar()
        result.append(FavoriteCategoryOut(
            id=cat.id, name=cat.name, created_at=cat.created_at, count=count or 0
        ))
    return result


@router.post("/categories", response_model=FavoriteCategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    data: FavoriteCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(FavoriteCategory).filter(
        FavoriteCategory.user_id == current_user.id,
        FavoriteCategory.name == data.name,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    cat = FavoriteCategory(user_id=current_user.id, name=data.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return FavoriteCategoryOut(id=cat.id, name=cat.name, created_at=cat.created_at, count=0)


@router.put("/categories/{category_id}", response_model=FavoriteCategoryOut)
def update_category(
    category_id: int,
    data: FavoriteCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = db.query(FavoriteCategory).filter(
        FavoriteCategory.id == category_id,
        FavoriteCategory.user_id == current_user.id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.name = data.name
    db.commit()
    db.refresh(cat)
    count = db.query(func.count(Favorite.id)).filter(Favorite.category_id == cat.id).scalar()
    return FavoriteCategoryOut(id=cat.id, name=cat.name, created_at=cat.created_at, count=count or 0)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = db.query(FavoriteCategory).filter(
        FavoriteCategory.id == category_id,
        FavoriteCategory.user_id == current_user.id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.query(Favorite).filter(Favorite.category_id == category_id).update({"category_id": None})
    db.delete(cat)
    db.commit()


@router.get("/status/{document_id}", response_model=FavoriteStatusOut)
def get_favorite_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.document_id == document_id,
    ).first()
    if fav:
        return FavoriteStatusOut(is_favorited=True, favorite_id=fav.id, category_id=fav.category_id)
    return FavoriteStatusOut(is_favorited=False)


@router.get("", response_model=list[FavoriteOut])
def list_favorites(
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Favorite).filter(Favorite.user_id == current_user.id)
    if category_id is not None:
        if category_id == 0:
            query = query.filter(Favorite.category_id == None)
        else:
            query = query.filter(Favorite.category_id == category_id)
    favorites = query.order_by(Favorite.created_at.desc()).all()
    return favorites


@router.post("", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def add_favorite(
    data: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == data.document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.document_id == data.document_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already favorited")

    if data.category_id:
        cat = db.query(FavoriteCategory).filter(
            FavoriteCategory.id == data.category_id,
            FavoriteCategory.user_id == current_user.id,
        ).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    fav = Favorite(
        user_id=current_user.id,
        document_id=data.document_id,
        category_id=data.category_id,
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fav = db.query(Favorite).filter(
        Favorite.id == favorite_id,
        Favorite.user_id == current_user.id,
    ).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()


@router.put("/{favorite_id}/category", response_model=FavoriteOut)
def move_favorite_category(
    favorite_id: int,
    data: FavoriteMoveCategory,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fav = db.query(Favorite).filter(
        Favorite.id == favorite_id,
        Favorite.user_id == current_user.id,
    ).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    if data.category_id:
        cat = db.query(FavoriteCategory).filter(
            FavoriteCategory.id == data.category_id,
            FavoriteCategory.user_id == current_user.id,
        ).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    fav.category_id = data.category_id
    db.commit()
    db.refresh(fav)
    return fav
