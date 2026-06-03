from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, check_document_access
from app.models.user import User
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.schemas.document_permission import DocumentPermissionCreate, DocumentPermissionOut

router = APIRouter()


@router.get("/{doc_id}/permissions", response_model=list[DocumentPermissionOut])
def list_permissions(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only document owner or admin can view permissions")
    return doc.permissions


@router.post("/{doc_id}/permissions", response_model=DocumentPermissionOut, status_code=status.HTTP_201_CREATED)
def grant_permission(
    doc_id: int,
    data: DocumentPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only document owner or admin can grant permissions")

    if data.permission_level not in ("read", "write", "admin"):
        raise HTTPException(status_code=422, detail="Permission level must be read, write, or admin")

    existing = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == doc_id,
        DocumentPermission.user_id == data.user_id,
    ).first()
    if existing:
        existing.permission_level = data.permission_level
        db.commit()
        db.refresh(existing)
        return existing

    perm = DocumentPermission(
        document_id=doc_id,
        user_id=data.user_id,
        permission_level=data.permission_level,
        granted_by=current_user.id,
    )
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


@router.delete("/{doc_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_permission(
    doc_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only document owner or admin can revoke permissions")

    perm = db.query(DocumentPermission).filter(
        DocumentPermission.id == permission_id,
        DocumentPermission.document_id == doc_id,
    ).first()
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")

    db.delete(perm)
    db.commit()
