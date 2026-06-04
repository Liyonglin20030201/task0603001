from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.project import Project
from app.models.subscription import Subscription
from app.models.notification import Notification
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionOut,
    NotificationOut,
    NotificationListResponse,
)

router = APIRouter()


@router.post("/subscriptions", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not data.document_id and not data.project_id:
        raise HTTPException(status_code=422, detail="Must provide document_id or project_id")
    if data.document_id and data.project_id:
        raise HTTPException(status_code=422, detail="Provide only one of document_id or project_id")

    if data.document_id:
        doc = db.query(Document).filter(Document.id == data.document_id, Document.is_deleted == False).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        existing = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.document_id == data.document_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Already subscribed to this document")

    if data.project_id:
        project = db.query(Project).filter(Project.id == data.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        existing = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.project_id == data.project_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Already subscribed to this project")

    sub = Subscription(
        user_id=current_user.id,
        document_id=data.document_id,
        project_id=data.project_id,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/subscriptions", response_model=list[SubscriptionOut])
def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Subscription).filter(Subscription.user_id == current_user.id).all()


@router.delete("/subscriptions/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(
        Subscription.id == sub_id, Subscription.user_id == current_user.id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(sub)
    db.commit()


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = db.query(Notification).filter(Notification.user_id == current_user.id)
    total = base_query.count()
    unread_count = base_query.filter(Notification.is_read == False).count()

    items = (
        base_query
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return NotificationListResponse(items=items, total=total, unread_count=unread_count)


@router.put("/notifications/{notif_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id, Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()


@router.put("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()


@router.delete("/notifications/{notif_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id, Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notif)
    db.commit()
