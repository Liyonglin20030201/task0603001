from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db, get_current_user, require_role, check_document_access
from app.models.user import User
from app.models.document import Document
from app.models.document_access_log import DocumentAccessLog
from app.models.document_version import DocumentVersion
from app.schemas.statistics import (
    SystemStatsOut,
    PopularDocumentOut,
    ActiveUserOut,
    DocumentStatsOut,
    AccessRecordOut,
    VersionHistoryOut,
)

router = APIRouter()


@router.get("/system", response_model=SystemStatsOut)
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    total_documents = db.query(func.count(Document.id)).filter(Document.is_deleted == False).scalar()
    total_visits = db.query(func.count(DocumentAccessLog.id)).scalar()
    total_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()

    popular_rows = (
        db.query(
            DocumentAccessLog.document_id,
            func.count(DocumentAccessLog.id).label("access_count"),
        )
        .group_by(DocumentAccessLog.document_id)
        .order_by(func.count(DocumentAccessLog.id).desc())
        .limit(10)
        .all()
    )
    popular_documents = []
    for row in popular_rows:
        doc = db.query(Document).filter(Document.id == row.document_id).first()
        if doc:
            popular_documents.append(
                PopularDocumentOut(
                    document_id=row.document_id,
                    title=doc.title,
                    access_count=row.access_count,
                )
            )

    active_rows = (
        db.query(
            DocumentAccessLog.user_id,
            func.count(DocumentAccessLog.id).label("access_count"),
        )
        .group_by(DocumentAccessLog.user_id)
        .order_by(func.count(DocumentAccessLog.id).desc())
        .limit(10)
        .all()
    )
    active_users = []
    for row in active_rows:
        user = db.query(User).filter(User.id == row.user_id).first()
        if user:
            active_users.append(
                ActiveUserOut(
                    user_id=row.user_id,
                    username=user.username,
                    access_count=row.access_count,
                )
            )

    return SystemStatsOut(
        total_documents=total_documents,
        total_visits=total_visits,
        total_users=total_users,
        popular_documents=popular_documents,
        active_users=active_users,
    )


@router.get("/documents/{doc_id}", response_model=DocumentStatsOut)
def get_document_stats(
    doc_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not check_document_access(doc, current_user, "read", db):
        raise HTTPException(status_code=403, detail="Access denied")

    total_accesses = (
        db.query(func.count(DocumentAccessLog.id))
        .filter(DocumentAccessLog.document_id == doc_id)
        .scalar()
    )

    access_logs = (
        db.query(DocumentAccessLog)
        .filter(DocumentAccessLog.document_id == doc_id)
        .order_by(DocumentAccessLog.accessed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    access_records = []
    for log in access_logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        access_records.append(
            AccessRecordOut(
                user_id=log.user_id,
                username=user.username if user else "unknown",
                accessed_at=log.accessed_at,
            )
        )

    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == doc_id)
        .order_by(DocumentVersion.version_number.desc())
        .all()
    )
    version_history = []
    for v in versions:
        uploader = db.query(User).filter(User.id == v.uploaded_by).first() if v.uploaded_by else None
        version_history.append(
            VersionHistoryOut(
                version_number=v.version_number,
                uploaded_by=v.uploaded_by,
                uploader_username=uploader.username if uploader else None,
                file_size=v.file_size,
                created_at=v.created_at,
            )
        )

    return DocumentStatsOut(
        document_id=doc_id,
        total_accesses=total_accesses,
        access_records=access_records,
        version_history=version_history,
    )
