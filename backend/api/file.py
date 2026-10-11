import os
import shutil
from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from utils.utils import get_current_user
from rag.pipeline import process_uploaded_file
from utils.file_hash import compute_file_hash
from sqlalchemy.orm import Session
from db.database import get_db  
from models.document import Document
from models.models import User
import uuid
import logging
from worker.queue import ingestion_queue
from worker.jobs import ingest_document_job

# Set up proper logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["files"])

Upload_DIR = "uploaded_files"
os.makedirs(Upload_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".md", ".csv"}
MAX_FILE_SIZE = 50 * 1024 * 1024

def validate_file(file: UploadFile):
    """Validate file type and size."""
    if not file or not file.filename:
        logger.error("No file provided or filename is empty")
        raise HTTPException(status_code=400, detail="No file provided")
    
    ext = os.path.splitext(file.filename)[1].lower() 
    if ext not in ALLOWED_EXTENSIONS:
        logger.error(f"Invalid file type: {ext} for file {file.filename}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {ext}. Allowed: PDF, TXT, DOCX, MD, CSV"
        )

    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        logger.error(f"File too large: {size} bytes (max: {MAX_FILE_SIZE})")
        raise HTTPException(status_code=400, detail="File too large. Max 50MB")
    
    if size == 0:
        logger.error("File is empty (0 bytes)")
        raise HTTPException(status_code=400, detail="File is empty")
    
    logger.info(f"✅ File validation passed: {file.filename} ({size} bytes)")

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"📤 Upload request from user: {current_user.get('email')}")
    logger.info(f"📄 File: {file.filename if file else 'NO FILE'}")
    
    try:
        # Step 1: Validate file
        validate_file(file)
        
        # Step 2: Read file bytes ONCE
        logger.info("Reading file bytes...")
        file_bytes = await file.read()
        logger.info(f"✅ Read {len(file_bytes)} bytes")
        
        # Step 3: Compute hash and check for duplicates 
        logger.info("Computing file hash...")
        file_hash = compute_file_hash(file_bytes)
        logger.info(f"✅ File hash: {file_hash}")
        
        # Get user from DB
        logger.info(f"Fetching user from DB: {current_user['email']}")
        user = db.query(User).filter(User.email == current_user["email"]).first()
        if not user:
            logger.error(f"User not found in DB: {current_user['email']}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ User found: ID={user.id}")
        
        # Check for duplicate - file_hash must be unique per user
        logger.info("Checking for duplicate file...")
        existing = db.query(Document).filter(
            Document.file_hash == file_hash,
            Document.user_id == user.id
        ).first()
        
        if existing:
            logger.warning(f"Duplicate file detected: {file_hash}")
            raise HTTPException(status_code=400, detail="File already uploaded by this user")
        
        logger.info("✅ No duplicate found")
        
        # Step 4: Create unique safe filename
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = f"{unique_id}_{file.filename.replace(' ','_')}"
        file_path = os.path.join(Upload_DIR, safe_filename)
        
        logger.info(f"Saving file to: {file_path}")
        
        # Step 5: Save file to disk using the bytes we already read
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)
            
        logger.info(f"✅ File saved: {file_path} ({len(file_bytes)} bytes)")

        # Step 6: Save to database
        logger.info("Saving document to database...")
        try:
            new_doc = Document(
                filename=file.filename,
                file_path=file_path,
                file_hash=file_hash,
                user_id=user.id,
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)

            document_id = new_doc.id
            logger.info(f"✅ Document saved in DB with ID: {document_id}")

        except Exception as db_error:
            db.rollback()
            logger.error(f"❌ DB save failed: {db_error}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")    
            
        # Step 7: Start background processing
        logger.info("Starting background processing task...")
        # background_tasks.add_task(
        #     process_uploaded_file,
        #     file_path=file_path,
        #     original_filename=file.filename,
        #     user_email=user.email,
        #     file_hash=file_hash,
        #     document_id=document_id
        # )
        ingestion_queue.enqueue(
            ingest_document_job,
            file_path,
            file.filename,
            user.email,
            file_hash,
            document_id,
        )    
        
        logger.info(f"🎉 Upload complete for document ID: {document_id}")
        
        # Step 8: Return success
        return JSONResponse({
            "message": "File uploaded & processing started",
            "document_id": document_id,
            "filename": file.filename,
            "size_kb": len(file_bytes) // 1024,
            "status": "processing"
        })
        
    except HTTPException as e:
        logger.error(f"HTTPException in upload: {e.status_code} - {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"❌ Unexpected upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))