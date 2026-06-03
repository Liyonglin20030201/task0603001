from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session


def init_fts_table(engine):
    with engine.connect() as conn:
        conn.execute(sa_text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                title, summary, content, tags,
                content='',
                tokenize='unicode61'
            )
        """))
        conn.commit()


def rebuild_fts_index(db: Session):
    from app.models.document import Document
    db.execute(sa_text("DELETE FROM documents_fts"))
    docs = db.query(Document).filter(Document.is_deleted == False).all()
    for doc in docs:
        tag_str = " ".join(t.name for t in doc.tags)
        db.execute(sa_text("""
            INSERT INTO documents_fts(rowid, title, summary, content, tags)
            VALUES (:id, :title, :summary, :content, :tags)
        """), {
            "id": doc.id,
            "title": doc.title or "",
            "summary": doc.summary or "",
            "content": doc.content or "",
            "tags": tag_str,
        })
    db.commit()


def update_fts_entry(db: Session, doc_id: int):
    from app.models.document import Document
    db.execute(sa_text("DELETE FROM documents_fts WHERE rowid = :id"), {"id": doc_id})
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc and not doc.is_deleted:
        tag_str = " ".join(t.name for t in doc.tags)
        db.execute(sa_text("""
            INSERT INTO documents_fts(rowid, title, summary, content, tags)
            VALUES (:id, :title, :summary, :content, :tags)
        """), {
            "id": doc.id,
            "title": doc.title or "",
            "summary": doc.summary or "",
            "content": doc.content or "",
            "tags": tag_str,
        })
    db.commit()


def delete_fts_entry(db: Session, doc_id: int):
    db.execute(sa_text("DELETE FROM documents_fts WHERE rowid = :id"), {"id": doc_id})
    db.commit()


def search_documents(db: Session, query: str, limit: int = 50, offset: int = 0):
    fts_query = query.replace('"', '""')
    results = db.execute(sa_text("""
        SELECT
            f.rowid as doc_id,
            rank as relevance,
            snippet(documents_fts, 0, '<mark>', '</mark>', '...', 32) as title_snippet,
            snippet(documents_fts, 1, '<mark>', '</mark>', '...', 48) as summary_snippet,
            snippet(documents_fts, 2, '<mark>', '</mark>', '...', 64) as content_snippet
        FROM documents_fts f
        WHERE documents_fts MATCH :query
        ORDER BY rank
        LIMIT :limit OFFSET :offset
    """), {"query": fts_query, "limit": limit, "offset": offset})
    return results.fetchall()


def count_search_results(db: Session, query: str) -> int:
    fts_query = query.replace('"', '""')
    result = db.execute(sa_text("""
        SELECT COUNT(*) FROM documents_fts WHERE documents_fts MATCH :query
    """), {"query": fts_query})
    return result.scalar() or 0
