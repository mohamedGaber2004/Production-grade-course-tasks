"""Dependency injection container for hexagonal architecture."""

from src.infrastructure.config.config import get_settings
from src.infrastructure.config.dependencies import get_vector_store
from src.infrastructure.adapters.database.qdrant_vector_store_adapter import QdrantVectorStoreAdapter
from src.infrastructure.adapters.chunking_adapter import LangChainChunkingAdapter
from src.infrastructure.adapters.metadata_adapter import ProductionMetadataAdapter
from src.infrastructure.adapters.crag_adapter import CRAGAdapter
from src.infrastructure.adapters.chunking import ChunkingStrategy
from src.infrastructure.adapters.metadata import ProductionEnricher
from src.infrastructure.adapters.crag import CRAGEvaluator
from src.application.services import RAGApplicationService


def create_rag_service() -> RAGApplicationService:
    """Create the RAG application service with all dependencies."""
    settings = get_settings()
    vector_store_connector = get_vector_store()
    vector_store_repo = QdrantVectorStoreAdapter(vector_store_connector)

    chunking_strategy = ChunkingStrategy(settings.chunking)
    chunking_service = LangChainChunkingAdapter(chunking_strategy)

    metadata_enricher = ProductionEnricher()
    metadata_service = ProductionMetadataAdapter(metadata_enricher)

    crag_evaluator = CRAGEvaluator()
    crag_service = CRAGAdapter(crag_evaluator)

    # Placeholder for LLM service
    llm_service = None

    # Placeholder for document repo
    document_repo = None

    return RAGApplicationService(
        vector_store_repo=vector_store_repo,
        document_repo=document_repo,
        chunking_service=chunking_service,
        metadata_service=metadata_service,
        crag_service=crag_service,
        llm_service=llm_service,
    )