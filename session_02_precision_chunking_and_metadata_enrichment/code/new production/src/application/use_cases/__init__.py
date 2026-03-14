"""Application use cases for the RAG system."""

from abc import ABC, abstractmethod
from typing import List, Protocol
from domain.entities import Document, Chunk, Query, RAGResponse
from domain.repositories import VectorStoreRepository, DocumentRepository
from domain.services import ChunkingService, MetadataEnrichmentService, CRAGEvaluatorService


class IngestDocumentsUseCase(ABC):
    """Use case for ingesting documents."""

    @abstractmethod
    def execute(self, documents: List[Document], enrich_metadata: bool = True) -> List[Chunk]:
        """Execute the ingest documents use case."""
        pass


class QueryRAGUseCase(ABC):
    """Use case for querying the RAG system."""

    @abstractmethod
    def execute(self, query: Query) -> RAGResponse:
        """Execute the query RAG use case."""
        pass


class CompareStrategiesUseCase(ABC):
    """Use case for comparing chunking strategies."""

    @abstractmethod
    def execute(self, query: str) -> Dict[str, Any]:
        """Execute the compare strategies use case."""
        pass