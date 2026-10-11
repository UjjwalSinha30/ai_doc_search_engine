from db.database import SessionLocal
from models.document import Document
from rag.pipeline import process_uploaded_file

def ingest_document_job(file_path, original_filename, user_email, file_hash, document_id):
    db = SessionLocal()

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "processing"
            doc.error_message = None
            db.commit()

        process_uploaded_file(
            file_path=file_path,
            original_filename=original_filename,
            user_email=user_email,
            file_hash=file_hash,
            document_id=document_id,
        )

        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "indexed"
            doc.error_message = None
            db.commit()
    except Exception as e:
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            db.rollback()
            doc.status = "failed"
            doc.error_message = str(e)[:500]
            db.commit()
            raise
    finally:
        db.close()
