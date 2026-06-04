from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_role, check_document_access
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.project import Project
from app.models.tag import Tag, document_tags
from app.schemas.batch import (
    BatchDeleteRequest,
    BatchMoveRequest,
    BatchTagRequest,
    BatchPermissionRequest,
    BatchResultOut,
    BatchErrorItem,
)

router = APIRouter()


@router.post("/delete", response_model=BatchResultOut)
def batch_delete(
    data: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    errors = []
    succeeded = 0

    for doc_id in data.document_ids:
        doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
        if not doc:
            errors.append(BatchErrorItem(document_id=doc_id, error="Document not found"))
            continue
        if not check_document_access(doc, current_user, "write", db):
            errors.append(BatchErrorItem(document_id=doc_id, error="Access denied"))
            continue
        doc.is_deleted = True
        doc.deleted_at = datetime.now(timezone.utc)
        succeeded += 1

    db.commit()
    return BatchResultOut(
        total=len(data.document_ids), succeeded=succeeded, failed=len(errors), errors=errors,
    )


@router.post("/move", response_model=BatchResultOut)
def batch_move(
    data: BatchMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Target project not found")

    errors = []
    succeeded = 0

    for doc_id in data.document_ids:
        doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
        if not doc:
            errors.append(BatchErrorItem(document_id=doc_id, error="Document not found"))
            continue
        if not check_document_access(doc, current_user, "write", db):
            errors.append(BatchErrorItem(document_id=doc_id, error="Access denied"))
            continue
        doc.project_id = data.project_id
        succeeded += 1

    db.commit()
    return BatchResultOut(
        total=len(data.document_ids), succeeded=succeeded, failed=len(errors), errors=errors,
    )


@router.post("/tags", response_model=BatchResultOut)
def batch_add_tags(
    data: BatchTagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    tags = []
    for tag_name in data.tag_names:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()
        tags.append(tag)

    errors = []
    succeeded = 0

    for doc_id in data.document_ids:
        doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
        if not doc:
            errors.append(BatchErrorItem(document_id=doc_id, error="Document not found"))
            continue
        if not check_document_access(doc, current_user, "write", db):
            errors.append(BatchErrorItem(document_id=doc_id, error="Access denied"))
            continue
        for tag in tags:
            if tag not in doc.tags:
                doc.tags.append(tag)
        succeeded += 1

    db.commit()
    return BatchResultOut(
        total=len(data.document_ids), succeeded=succeeded, failed=len(errors), errors=errors,
    )


@router.post("/permissions", response_model=BatchResultOut)
def batch_set_permissions(
    data: BatchPermissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if data.permission_level not in ("read", "write", "admin"):
        raise HTTPException(status_code=422, detail="Invalid permission level")

    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    errors = []
    succeeded = 0

    for doc_id in data.document_ids:
        doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
        if not doc:
            errors.append(BatchErrorItem(document_id=doc_id, error="Document not found"))
            continue

        existing = db.query(DocumentPermission).filter(
            DocumentPermission.document_id == doc_id,
            DocumentPermission.user_id == data.user_id,
        ).first()

        if existing:
            existing.permission_level = data.permission_level
        else:
            perm = DocumentPermission(
                document_id=doc_id,
                user_id=data.user_id,
                permission_level=data.permission_level,
                granted_by=current_user.id,
            )
            db.add(perm)
        succeeded += 1

    db.commit()
    return BatchResultOut(
        total=len(data.document_ids), succeeded=succeeded, failed=len(errors), errors=errors,
    )
