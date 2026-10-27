
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)


def chunk_text(
    text: str,
    strategy: str = "recursive",
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[str]:
    """Split document text using one of two strategies."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative "
            "and smaller than chunk_size"
        )

    if not text.strip():
        return []

    if strategy == "fixed_size":
        chunks = [
            text[i : i + chunk_size]
            for i in range(0, len(text), chunk_size - chunk_overlap)
        ]
        return chunks

    if strategy == "recursive":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_text(text)

    raise ValueError(
        "Unsupported strategy. Use 'fixed_size' or 'recursive'."
    )

