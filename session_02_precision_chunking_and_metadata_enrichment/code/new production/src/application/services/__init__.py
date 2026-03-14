"""Application services implementing the use cases."""

from typing import List, Dict, Any
from domain.entities import Document, Chunk, Query, RAGResponse
from domain.repositories import VectorStoreRepository, DocumentRepository
from domain.services import ChunkingService, MetadataEnrichmentService, CRAGEvaluatorService
from application.use_cases import IngestDocumentsUseCase, QueryRAGUseCase, CompareStrategiesUseCase


class RAGApplicationService(IngestDocumentsUseCase, QueryRAGUseCase, CompareStrategiesUseCase):
    """Application service for RAG operations."""

    def __init__(
        self,
        vector_store_repo: VectorStoreRepository,
        document_repo: DocumentRepository,
        chunking_service: ChunkingService,
        metadata_service: MetadataEnrichmentService,
        crag_service: CRAGEvaluatorService,
        llm_service: Any,  # Placeholder for LLM service
    ):
        self.vector_store_repo = vector_store_repo
        self.document_repo = document_repo
        self.chunking_service = chunking_service
        self.metadata_service = metadata_service
        self.crag_service = crag_service
        self.llm_service = llm_service

    def execute_ingest(self, documents: List[Document], enrich_metadata: bool = True) -> List[Chunk]:
        """Execute document ingestion."""
        all_chunks = []
        for doc in documents:
            self.document_repo.save(doc)
            chunks = self.chunking_service.chunk_document(doc)
            if enrich_metadata:
                chunks = self.metadata_service.enrich_metadata(chunks)
            self.vector_store_repo.store_chunks(chunks)
            all_chunks.extend(chunks)
        return all_chunks

    def execute_query(self, query: Query) -> RAGResponse:
        """Execute RAG query."""
        # This would implement the full RAG pipeline
        # For now, placeholder
        return RAGResponse(answer="Placeholder", sources=[], confidence=0.0)

    def execute_compare(self, query: str) -> Dict[str, Any]:
        """Execute strategy comparison."""
        # Placeholder
        return {}