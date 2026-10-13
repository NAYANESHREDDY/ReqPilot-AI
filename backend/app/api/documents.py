import uuid
import shutil
from pathlib import Path
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models import Document, DocumentChunk, Project
from backend.app.schemas import DocumentResponse, DocumentChunkResponse
from backend.app.config import UPLOAD_DIR
from backend.app.agents.ingestion_agent import IngestionAgent

router = APIRouter(tags=["documents"])
ingestion_agent = IngestionAgent()

@router.get("/api/projects/{project_id}/documents", response_model=List[DocumentResponse])
async def list_project_documents(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.project_id == project_id).options(selectinload(Document.chunks))
    )
    return result.scalars().all()

@router.post("/api/projects/{project_id}/documents/upload", response_model=DocumentResponse)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    proj_res = await db.execute(select(Project).where(Project.id == project_id))
    if not proj_res.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found")

    filename = file.filename or "uploaded_file.txt"
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ["pdf", "docx", "doc", "txt", "md"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, TXT, or Markdown.")

    doc_id = str(uuid.uuid4())
    stored_path = UPLOAD_DIR / f"{doc_id}_{filename}"

    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = stored_path.stat().st_size

    new_doc = Document(
        id=doc_id,
        project_id=project_id,
        filename=filename,
        file_type=ext,
        file_size=file_size,
        storage_path=str(stored_path),
        status="parsing",
        created_at=datetime.utcnow(),
    )
    db.add(new_doc)
    await db.flush()

    # Ingestion & Chunking
    parsed_chunks = ingestion_agent.parse_file(stored_path, filename)
    chunk_records = []
    for c in parsed_chunks:
        chunk_rec = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=new_doc.id,
            project_id=project_id,
            chunk_index=c["chunk_index"],
            section_title=c["section_title"],
            page_number=c["page_number"],
            content=c["content"],
            token_count=c["token_count"],
            created_at=datetime.utcnow(),
        )
        chunk_records.append(chunk_rec)

    db.add_all(chunk_records)
    new_doc.status = "processed"
    await db.commit()

    # Load with chunks
    res = await db.execute(
        select(Document).where(Document.id == new_doc.id).options(selectinload(Document.chunks))
    )
    return res.scalars().first()

@router.get("/api/documents/{id}", response_model=DocumentResponse)
async def get_document(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.id == id).options(selectinload(Document.chunks))
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
