from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.database import SessionLocal
from app.config import settings
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except (jwt.PyJWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker


def check_document_access(doc, user: User, required_level: str, db: Session) -> bool:
    if user.role == "admin":
        return True
    if doc.owner_id == user.id:
        return True

    from app.models.document_permission import DocumentPermission
    explicit_perms = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == doc.id
    ).all()

    if explicit_perms:
        user_perm = next((p for p in explicit_perms if p.user_id == user.id), None)
        if not user_perm:
            return False
        level_hierarchy = {"read": 1, "write": 2, "admin": 3}
        return level_hierarchy.get(user_perm.permission_level, 0) >= level_hierarchy.get(required_level, 0)
    else:
        role_level = {"viewer": 1, "editor": 2, "admin": 3}
        required_map = {"read": 1, "write": 2, "admin": 3}
        return role_level.get(user.role, 0) >= required_map.get(required_level, 0)
