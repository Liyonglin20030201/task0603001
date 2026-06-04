import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_role, check_document_access
from app.models.user import User
from app.models.document import Document
from app.models.share_link import ShareLink
from app.schemas.share import ShareLinkCreate, ShareLinkOut, ShareAccessRequest, SharedDocumentOut
from app.services.auth_service import hash_password, verify_password

router = APIRouter()


@router.post("/documents/{doc_id}/shares", response_model=ShareLinkOut, status_code=status.HTTP_201_CREATED)
def create_share_link(
    doc_id: int,
    data: ShareLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "editor")),
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not check_document_access(doc, current_user, "write", db):
        raise HTTPException(status_code=403, detail="Access denied")

    if not data.is_permanent and not data.expires_at:
        raise HTTPException(status_code=422, detail="Temporary links must have an expiration date")

    token = secrets.token_urlsafe(32)
    password_hash = hash_password(data.password) if data.password else None

    share = ShareLink(
        document_id=doc_id,
        token=token,
        created_by=current_user.id,
        is_permanent=data.is_permanent,
        expires_at=data.expires_at,
        max_access_count=data.max_access_count,
        password_hash=password_hash,
        is_active=True,
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    return ShareLinkOut(
        id=share.id,
        document_id=share.document_id,
        token=share.token,
        is_permanent=share.is_permanent,
        expires_at=share.expires_at,
        max_access_count=share.max_access_count,
        current_access_count=share.current_access_count,
        has_password=share.password_hash is not None,
        is_active=share.is_active,
        created_at=share.created_at,
    )


@router.get("/documents/{doc_id}/shares", response_model=list[ShareLinkOut])
def list_share_links(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    shares = db.query(ShareLink).filter(ShareLink.document_id == doc_id).all()
    return [
        ShareLinkOut(
            id=s.id,
            document_id=s.document_id,
            token=s.token,
            is_permanent=s.is_permanent,
            expires_at=s.expires_at,
            max_access_count=s.max_access_count,
            current_access_count=s.current_access_count,
            has_password=s.password_hash is not None,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in shares
    ]


@router.delete("/documents/{doc_id}/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_share_link(
    doc_id: int,
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    share = db.query(ShareLink).filter(
        ShareLink.id == share_id, ShareLink.document_id == doc_id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share link not found")

    share.is_active = False
    db.commit()


def _validate_share_link(share: ShareLink) -> None:
    if not share.is_active:
        raise HTTPException(status_code=410, detail="Share link is no longer active")
    if share.expires_at:
        now = datetime.now(timezone.utc)
        expires = share.expires_at if share.expires_at.tzinfo else share.expires_at.replace(tzinfo=timezone.utc)
        if expires < now:
            raise HTTPException(status_code=410, detail="Share link has expired")
    if share.max_access_count and share.current_access_count >= share.max_access_count:
        raise HTTPException(status_code=410, detail="Share link access limit reached")


@router.get("/shared/{token}", response_model=SharedDocumentOut)
def access_shared_document(
    token: str,
    db: Session = Depends(get_db),
):
    share = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share link not found")

    _validate_share_link(share)

    if share.password_hash:
        raise HTTPException(status_code=403, detail="Password required")

    doc = db.query(Document).filter(Document.id == share.document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    share.current_access_count += 1
    db.commit()

    return doc


@router.post("/shared/{token}/verify", response_model=SharedDocumentOut)
def verify_shared_document(
    token: str,
    data: ShareAccessRequest,
    db: Session = Depends(get_db),
):
    share = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share link not found")

    _validate_share_link(share)

    if not share.password_hash:
        raise HTTPException(status_code=400, detail="This link does not require a password")

    if not verify_password(data.password, share.password_hash):
        raise HTTPException(status_code=403, detail="Invalid password")

    doc = db.query(Document).filter(Document.id == share.document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    share.current_access_count += 1
    db.commit()

    return doc
