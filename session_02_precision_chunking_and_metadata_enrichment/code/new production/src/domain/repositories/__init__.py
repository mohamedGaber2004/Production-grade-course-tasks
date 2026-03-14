"""Repository interfaces for the domain."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from domain.entities import Chunk, Document


class VectorStoreRepository(ABC):
    """Interface for vector store operations."""

    @abstractmethod
    def store_chunks(self, chunks: List[Chunk]) -> None:
        """Store chunks in the vector store."""
        pass

    @abstractmethod
    def search_similar(self, query_embedding: List[float], top_k: int = 10, filters: Dict[str, Any] = None) -> List[Chunk]:
        """Search for similar chunks."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the vector store is healthy."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if the vector store is ready."""
        pass


class DocumentRepository(ABC):
    """Interface for document operations."""

    @abstractmethod
    def save(self, document: Document) -> None:
        """Save a document."""
        pass

    @abstractmethod
    def get_by_id(self, document_id: str) -> Document | None:
        """Get a document by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Document]:
        """Get all documents."""
        pass