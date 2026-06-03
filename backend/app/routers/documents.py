from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional
import math

from app.dependencies import get_db, get_current_user, require_role, check_document_access
from app.models.user import User
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.schemas.document import DocumentOut, DocumentUpdate, DocumentListResponse, DocumentVersionOut
from app.services.document_service import process_upload, upload_new_version, rollback_to_version

router = APIRouter()

ALLOWED_TYPES = {"pdf", "docx", "pptx", "doc", "ppt", "xlsx", "xls", "txt", "md"}


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    project_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=422, detail=f"File type must be one of: {ALLOWED_TYPES}")

    file_bytes = file.file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File too large (max 50MB)")

    doc = process_upload(
        db=db,
        file_bytes=file_bytes,
        original_filename=file.filename,
        title=title,
        file_type=ext,
        owner_id=current_user.id,
        project_id=project_id,
    )
    return doc


@router.get("", response_model=DocumentListResponse)
def list_documents(
    project_id: Optional[int] = Query(None),
    owner_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document).filter(Document.is_deleted == False)

    if project_id:
        query = query.filter(Document.project_id == project_id)
    if owner_id:
        query = query.filter(Document.owner_id == owner_id)
    if date_from:
        query = query.filter(Document.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Document.created_at <= datetime.fromisoformat(date_to))
    if tag:
        from app.models.tag import Tag
        query = query.join(Document.tags).filter(Tag.name == tag)
    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    items = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return DocumentListResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/trash", response_model=list[DocumentOut])
def list_trash(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return db.query(Document).filter(Document.is_deleted == True).all()


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not check_document_access(doc, current_user, "read", db):
        raise HTTPException(status_code=403, detail="Access denied")
    return doc


@router.put("/{doc_id}", response_model=DocumentOut)
def update_document(
    doc_id: int,
    update_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if update_data.title is not None:
        doc.title = update_data.title
    if update_data.project_id is not None:
        doc.project_id = update_data.project_id

    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    doc.is_deleted = True
    doc.deleted_at = datetime.utcnow()
    db.commit()


@router.post("/{doc_id}/restore", response_model=DocumentOut)
def restore_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == True).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in trash")
    doc.is_deleted = False
    doc.deleted_at = None
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{doc_id}/versions", response_model=DocumentVersionOut, status_code=status.HTTP_201_CREATED)
def create_version(
    doc_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    file_bytes = file.file.read()
    version = upload_new_version(db, doc, file_bytes, file.filename, current_user.id)
    return version


@router.get("/{doc_id}/versions", response_model=list[DocumentVersionOut])
def list_versions(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.versions


@router.get("/{doc_id}/versions/{version_number}/download")
def download_version(
    doc_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == doc_id,
        DocumentVersion.version_number == version_number,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return FileResponse(version.file_path, filename=version.file_path.split(os.sep)[-1])


@router.post("/{doc_id}/versions/{version_number}/rollback", response_model=DocumentOut)
def rollback_version(
    doc_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    if doc.current_version == version_number:
        raise HTTPException(status_code=400, detail="Already at this version")

    try:
        doc = rollback_to_version(db, doc, version_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return doc


@router.get("/{doc_id}/preview")
def get_preview(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    latest_version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == doc_id,
        DocumentVersion.version_number == doc.current_version,
    ).first()

    if not latest_version or not latest_version.preview_path:
        raise HTTPException(status_code=404, detail="Preview not available")

    return FileResponse(latest_version.preview_path, media_type="application/pdf")


import os
