import os
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.tag import Tag, document_tags
from app.services.parser_service import extract_text
from app.services.nlp_service import generate_summary, extract_tags
from app.services.converter_service import convert_to_pdf


def process_upload(
    db: Session,
    file_bytes: bytes,
    original_filename: str,
    title: str,
    file_type: str,
    owner_id: int,
    project_id: Optional[int] = None,
) -> Document:
    doc = Document(
        title=title,
        original_filename=original_filename,
        file_type=file_type,
        owner_id=owner_id,
        project_id=project_id,
        current_version=1,
    )
    db.add(doc)
    db.flush()

    file_dir = os.path.join(settings.UPLOAD_DIR, str(doc.id), "v1")
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(file_dir, original_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    preview_dir = os.path.join(settings.PREVIEW_DIR, str(doc.id), "v1")
    preview_path = convert_to_pdf(file_path, preview_dir)

    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        file_path=file_path,
        preview_path=preview_path,
        file_size=len(file_bytes),
        uploaded_by=owner_id,
    )
    db.add(version)

    text = extract_text(file_path, file_type)
    if text:
        doc.content = text
        doc.summary = generate_summary(text)
        tag_names = extract_tags(text)
        for tag_name in tag_names:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            doc.tags.append(tag)

    db.commit()
    db.refresh(doc)

    from app.services.search_service import update_fts_entry
    update_fts_entry(db, doc.id)

    return doc


def upload_new_version(
    db: Session,
    doc: Document,
    file_bytes: bytes,
    original_filename: str,
    uploaded_by: int,
) -> DocumentVersion:
    new_version_num = doc.current_version + 1
    doc.current_version = new_version_num

    file_dir = os.path.join(settings.UPLOAD_DIR, str(doc.id), f"v{new_version_num}")
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(file_dir, original_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    preview_dir = os.path.join(settings.PREVIEW_DIR, str(doc.id), f"v{new_version_num}")
    preview_path = convert_to_pdf(file_path, preview_dir)

    version = DocumentVersion(
        document_id=doc.id,
        version_number=new_version_num,
        file_path=file_path,
        preview_path=preview_path,
        file_size=len(file_bytes),
        uploaded_by=uploaded_by,
    )
    db.add(version)

    text = extract_text(file_path, doc.file_type)
    if text:
        doc.content = text
        doc.summary = generate_summary(text)
        doc.tags.clear()
        tag_names = extract_tags(text)
        for tag_name in tag_names:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            doc.tags.append(tag)

    db.commit()
    db.refresh(version)

    from app.services.search_service import update_fts_entry
    update_fts_entry(db, doc.id)

    return version


def rollback_to_version(db: Session, doc: Document, target_version_number: int) -> Document:
    version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == doc.id,
        DocumentVersion.version_number == target_version_number,
    ).first()
    if not version:
        raise ValueError(f"Version {target_version_number} does not exist")

    doc.current_version = target_version_number

    text = extract_text(version.file_path, doc.file_type)
    if text:
        doc.content = text
        doc.summary = generate_summary(text)
        doc.tags.clear()
        tag_names = extract_tags(text)
        for tag_name in tag_names:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            doc.tags.append(tag)
    else:
        doc.content = None
        doc.summary = None
        doc.tags.clear()

    db.commit()
    db.refresh(doc)

    from app.services.search_service import update_fts_entry
    update_fts_entry(db, doc.id)

    return doc
