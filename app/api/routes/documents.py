
from uuid import uuid4
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import DocumentMetadata
from app.db.session import get_db
from app.schemas.document import IngestionResponse
from app.services.chunking import chunk_text
from app.services.ingestion import extract_document_text
from app.services.embeddings import create_embedding
from app.vectorstore.qdrant_store import create_collection, upsert_chunks

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_document(
    file: Annotated[UploadFile, File(description="PDF or TXT document")],
    strategy: Annotated[str, Form(description="fixed_size or recursive")] = "recursive",
    chunk_size: Annotated[int, Form(ge=100, le=5000)] = 1000,
    chunk_overlap: Annotated[int, Form(ge=0, le=999)] = 150,
    db: Session = Depends(get_db),
) -> IngestionResponse:
    """Extract, chunk, embed, store vectors, and save SQL metadata."""

    if strategy not in {"fixed_size", "recursive"}:
        raise HTTPException(
            status_code=422,
            detail="Strategy must be fixed_size or recursive.",
        )

    if chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=422,
            detail="chunk_overlap must be smaller than chunk_size.",
        )

    filename, text = await extract_document_text(file)

    chunks = chunk_text(
        text,
        strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No document chunks were generated.",
        )

    document_id = str(uuid4())

    # First: generate embeddings and store chunks in Qdrant.
    try:
        first_embedding = await create_embedding(chunks[0])
        await create_collection(len(first_embedding))

        embeddings = [first_embedding]
        for chunk in chunks[1:]:
            embeddings.append(await create_embedding(chunk))

        result = await upsert_chunks(
            chunks=chunks,
            embeddings=embeddings,
            document_id=document_id,
            filename=filename,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Document processing or vector storage failed. "
                "Check Gemini and Qdrant configuration."
            ),
        ) from exc

    # Second: save document metadata in SQLite.
    file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"

    metadata = DocumentMetadata(
        document_id=document_id,
        filename=filename,
        file_type=file_type,
        chunking_strategy=strategy,
        chunk_count=len(chunks),
    )

    try:
        db.add(metadata)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                "Vectors were stored, but saving document metadata failed. "
                "Check the SQL database."
            ),
        ) from exc

    return IngestionResponse(
        document_id=document_id,
        filename=filename,
        strategy=strategy,
        character_count=len(text),
        chunk_count=len(chunks),
        status="processed",
        message=(
            f"Document embedded and stored in Qdrant: "
            f"{result.get('count', len(chunks))} chunks. "
            "Metadata saved in SQLite."
        ),
    )
