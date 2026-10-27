
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def extract_document_text(file: UploadFile) -> tuple[str, str]:
    """Extract text from an uploaded PDF or TXT document."""
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in {".pdf", ".txt"}:
        raise HTTPException(
            status_code=415,
            detail="Only PDF and TXT files are supported.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(status_code=400, detail="File is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 10 MB.",
        )

    try:
        if extension == ".txt":
            text = content.decode("utf-8-sig")

        else:
            reader = PdfReader(BytesIO(content))

            if reader.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="Encrypted PDFs are not supported.",
                )

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the uploaded file.",
        ) from exc

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the document.",
        )

    return filename, text
