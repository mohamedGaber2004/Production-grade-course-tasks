"""Qdrant vector store adapter implementing the repository interface."""

from typing import List, Dict, Any
from domain.entities import Chunk
from domain.repositories import VectorStoreRepository
from infrastructure.adapters.database.vector_store import VectorStoreConnector


class QdrantVectorStoreAdapter(VectorStoreRepository):
    """Adapter for Qdrant vector store."""

    def __init__(self, connector: VectorStoreConnector):
        self.connector = connector

    def store_chunks(self, chunks: List[Chunk]) -> None:
        """Store chunks in Qdrant."""
        # Convert domain chunks to langchain documents or whatever the connector expects
        documents = []
        for chunk in chunks:
            doc = {
                'id': chunk.id,
                'content': chunk.content,
                'metadata': {
                    **chunk.metadata,
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index,
                },
                'embedding': chunk.embedding,
            }
            documents.append(doc)
        self.connector.store_documents(documents)

    def search_similar(self, query_embedding: List[float], top_k: int = 10, filters: Dict[str, Any] = None) -> List[Chunk]:
        """Search for similar chunks."""
        results = self.connector.search_similar(query_embedding, top_k, filters or {})
        chunks = []
        for result in results:
            chunk = Chunk(
                id=result['id'],
                content=result['content'],
                document_id=result['metadata'].get('document_id', ''),
                chunk_index=result['metadata'].get('chunk_index', 0),
                metadata=result['metadata'],
                embedding=result.get('embedding'),
            )
            chunks.append(chunk)
        return chunks

    def health_check(self) -> bool:
        """Check health."""
        return self.connector.health_check()

    def is_ready(self) -> bool:
        """Check if ready."""
        return self.connector.is_ready