"""Domain services for chunking and metadata enrichment."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from domain.entities import Document, Chunk


class ChunkingService(ABC):
    """Interface for chunking strategies."""

    @abstractmethod
    def chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk a document into smaller pieces."""
        pass


class MetadataEnrichmentService(ABC):
    """Interface for metadata enrichment."""

    @abstractmethod
    def enrich_metadata(self, chunks: List[Chunk]) -> List[Chunk]:
        """Enrich chunks with additional metadata."""
        pass


class CRAGEvaluatorService(ABC):
    """Interface for CRAG evaluation."""

    @abstractmethod
    def evaluate_and_rerank(self, query: str, chunks: List[Chunk]) -> List[Chunk]:
        """Evaluate and rerank chunks using CRAG."""
        pass