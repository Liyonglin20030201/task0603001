from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, documents, comments, projects, tags, users, document_permissions, search, favorites, statistics, shares, batch, subscriptions
from app.services.search_service import init_fts_table

Base.metadata.create_all(bind=engine)
init_fts_table(engine)

app = FastAPI(title="Knowledge Base API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(batch.router, prefix="/api/documents/batch", tags=["batch"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(comments.router, prefix="/api/documents", tags=["comments"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(document_permissions.router, prefix="/api/documents", tags=["permissions"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(favorites.router, prefix="/api/favorites", tags=["favorites"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(shares.router, prefix="/api", tags=["shares"])
app.include_router(subscriptions.router, prefix="/api", tags=["subscriptions"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
