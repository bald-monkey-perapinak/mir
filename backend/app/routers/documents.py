import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.auth_deps import require_admin, get_current_user
from app.database import get_db
from app.models import Document, User, JobStatus
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_FORMATS = {"pdf", "docx", "txt"}

class DocumentResponse(BaseModel):
    id: str
    title: str
    original_name: str
    file_format: str
    status: str
    chunk_count: int
    scenario_count: int
    created_at: str
    error_message: Optional[str] = None

async def run_document_processing(doc_id: str, file_path: str, file_format: str):
                                            
    from app.database import AsyncSessionLocal
    from app.processor import process_document
    from app.models import Document

    async with AsyncSessionLocal() as db:
        try:
            await db.execute(
                update(Document).where(Document.id ==
                                       doc_id).values(status="processing")
            )
            await db.commit()

            chunk_count = await process_document(doc_id, file_path, file_format, db)
            logger.info(f"Document {doc_id} processed: {chunk_count} chunks")

        except Exception as e:
            logger.error(f"Document processing failed for {doc_id}: {e}")
            async with AsyncSessionLocal() as db2:
                await db2.execute(
                    update(Document)
                    .where(Document.id == doc_id)
                    .values(status="error", error_message=str(e))
                )
                await db2.commit()

async def run_scenario_generation(doc_id: str):
                                              
    from app.database import AsyncSessionLocal
    from app.scenario_generator import generate_scenarios_for_document
    from app.models import Document

    async with AsyncSessionLocal() as db:
        try:
            await db.execute(
                update(Document).where(Document.id ==
                                       doc_id).values(status="generating")
            )
            await db.commit()

            count = await generate_scenarios_for_document(doc_id, db)
            logger.info(f"Generated {count} scenarios for document {doc_id}")

        except Exception as e:
            logger.error(f"Scenario generation failed for {doc_id}: {e}")
            async with AsyncSessionLocal() as db2:
                await db2.execute(
                    update(Document)
                    .where(Document.id == doc_id)
                    .values(status="error", error_message=str(e))
                )
                await db2.commit()

@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return [_to_response(d) for d in docs]

@router.get("/available")
async def list_available_documents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
                                                           
    result = await db.execute(
        select(Document)
        .where(Document.status == "scenarios_ready")
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [_to_response(d) for d in docs]

@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    ext = file.filename.rsplit(
        ".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_FORMATS:
        raise HTTPException(
            400, f"Unsupported format. Allowed: {', '.join(ALLOWED_FORMATS)}")

                     
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            400, f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB")

               
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.{ext}")
    with open(file_path, "wb") as f:
        f.write(content)

                      
    doc = Document(
        title=title,
        original_name=file.filename,
        file_path=file_path,
        file_format=ext,
        status="pending",
        created_by=admin.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

                                 
    background_tasks.add_task(run_document_processing, doc.id, file_path, ext)

    return _to_response(doc)

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await _get_doc_or_404(doc_id, db)
    return _to_response(doc)

@router.post("/{doc_id}/generate")
async def generate_scenarios(
    doc_id: str,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    doc = await _get_doc_or_404(doc_id, db)
    if doc.status not in ("indexed",):
        raise HTTPException(
            409, f"Document must be indexed first. Current status: {doc.status}")

    background_tasks.add_task(run_scenario_generation, doc.id)
    return {"message": "Scenario generation started", "document_id": doc_id}

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    doc = await _get_doc_or_404(doc_id, db)
                 
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await db.delete(doc)
    await db.commit()
    return {"message": "Deleted"}

                                                                                

async def _get_doc_or_404(doc_id: str, db: AsyncSession) -> Document:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc

def _to_response(d: Document) -> DocumentResponse:
    return DocumentResponse(
        id=d.id,
        title=d.title,
        original_name=d.original_name or "",
        file_format=d.file_format or "",
        status=d.status,
        chunk_count=d.chunk_count,
        scenario_count=d.scenario_count,
        created_at=d.created_at.isoformat() if d.created_at else "",
        error_message=d.error_message,
    )
