import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy import text as sa_text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token
from app.services.search_service import init_fts_table

TEST_DB_URL = "sqlite:///./test_kb.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    init_fts_table(engine)
    yield
    with engine.connect() as conn:
        conn.execute(sa_text("DROP TABLE IF EXISTS documents_fts"))
        conn.commit()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    from starlette.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def create_test_user(db, username="testuser", role="editor"):
    user = User(
        username=username,
        email=f"{username}@test.com",
        hashed_password=hash_password("password123"),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(user):
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db):
    return create_test_user(db, "admin", "admin")


@pytest.fixture
def editor_user(db):
    return create_test_user(db, "editor", "editor")


@pytest.fixture
def viewer_user(db):
    return create_test_user(db, "viewer", "viewer")


@pytest.fixture
def admin_headers(admin_user):
    return get_auth_headers(admin_user)


@pytest.fixture
def editor_headers(editor_user):
    return get_auth_headers(editor_user)


@pytest.fixture
def viewer_headers(viewer_user):
    return get_auth_headers(viewer_user)


@pytest.fixture
def sample_pdf():
    content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Hello World) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000236 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
330
%%EOF"""
    return content
