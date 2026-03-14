"""Domain entities for the RAG system."""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Document:
    """Represents a document in the system."""
    id: str
    content: str
    filename: str
    doc_type: str
    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class Chunk:
    """Represents a chunk of a document."""
    id: str
    content: str
    document_id: str
    chunk_index: int
    metadata: Dict[str, Any]
    embedding: List[float] | None = None


@dataclass
class Query:
    """Represents a user query."""
    content: str
    audience: str | None = None


@dataclass
class RAGResponse:
    """Represents a response from the RAG system."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float