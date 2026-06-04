from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.subscription import Subscription
from app.models.notification import Notification


def notify_subscribers(
    db: Session,
    document_id: int,
    event_type: str,
    actor_id: int,
    message: str,
):
    doc_subs = db.query(Subscription).filter(
        Subscription.document_id == document_id,
        Subscription.user_id != actor_id,
    ).all()

    doc = db.query(Document).filter(Document.id == document_id).first()
    project_subs = []
    if doc and doc.project_id:
        project_subs = db.query(Subscription).filter(
            Subscription.project_id == doc.project_id,
            Subscription.user_id != actor_id,
        ).all()

    user_ids = set()
    for sub in doc_subs + project_subs:
        user_ids.add(sub.user_id)

    for uid in user_ids:
        notif = Notification(
            user_id=uid,
            event_type=event_type,
            document_id=document_id,
            actor_id=actor_id,
            message=message,
        )
        db.add(notif)
    db.flush()
