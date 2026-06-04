from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut
from app.services.notification_service import notify_subscribers

router = APIRouter()


@router.get("/{doc_id}/comments", response_model=list[CommentOut])
def list_comments(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.comments


@router.post("/{doc_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    doc_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    comment = Comment(document_id=doc_id, user_id=current_user.id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    notify_subscribers(db, doc_id, "new_comment", current_user.id, f"文档 '{doc.title}' 收到了新评论")
    db.commit()

    return comment


@router.put("/{doc_id}/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    doc_id: int,
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.document_id == doc_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot edit others' comments")

    comment.content = data.content
    comment.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{doc_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    doc_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.document_id == doc_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot delete others' comments")

    db.delete(comment)
    db.commit()
