import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.schemas.search import SearchResponse, SearchResultItem
from app.services.search_service import search_documents, count_search_results

router = APIRouter()


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    results = search_documents(db, q, page_size, offset)
    total = count_search_results(db, q)

    items = []
    for row in results:
        doc = db.query(Document).filter(Document.id == row.doc_id).first()
        if not doc:
            continue

        if current_user.role != "admin":
            docs_with_perms = (
                select(DocumentPermission.document_id)
                .distinct()
                .scalar_subquery()
            )
            user_permitted_docs = (
                select(DocumentPermission.document_id)
                .where(DocumentPermission.user_id == current_user.id)
                .scalar_subquery()
            )
            is_owner = doc.owner_id == current_user.id
            has_no_perms = db.execute(
                select(DocumentPermission).where(DocumentPermission.document_id == doc.id)
            ).first() is None
            has_user_perm = db.execute(
                select(DocumentPermission).where(
                    DocumentPermission.document_id == doc.id,
                    DocumentPermission.user_id == current_user.id,
                )
            ).first() is not None

            if not (is_owner or has_no_perms or has_user_perm):
                continue

        items.append(SearchResultItem(
            id=doc.id,
            title=doc.title,
            file_type=doc.file_type,
            title_highlight=row.title_snippet or doc.title,
            summary_highlight=row.summary_snippet or "",
            content_highlight=row.content_snippet or "",
            relevance=abs(row.relevance) if row.relevance else 0,
            tags=[t.name for t in doc.tags],
            created_at=doc.created_at,
        ))

    return SearchResponse(items=items, query=q, total=total, page=page, page_size=page_size)
