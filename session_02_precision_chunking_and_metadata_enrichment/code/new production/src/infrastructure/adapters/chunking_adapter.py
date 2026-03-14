"""Chunking adapter implementing the domain service."""

from typing import List
from domain.entities import Document, Chunk
from domain.services import ChunkingService
from infrastructure.adapters.chunking import ChunkingStrategy


class LangChainChunkingAdapter(ChunkingService):
    """Adapter for LangChain chunking strategies."""

    def __init__(self, chunking_strategy: ChunkingStrategy):
        self.chunking_strategy = chunking_strategy

    def chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk the document using the configured strategy."""
        # Convert domain document to langchain document
        langchain_doc = {
            'content': document.content,
            'metadata': document.metadata,
        }
        chunked_docs = self.chunking_strategy.chunk([langchain_doc])

        chunks = []
        for i, chunk_doc in enumerate(chunked_docs):
            chunk = Chunk(
                id=f"{document.id}_chunk_{i}",
                content=chunk_doc['content'],
                document_id=document.id,
                chunk_index=i,
                metadata=chunk_doc['metadata'],
            )
            chunks.append(chunk)
        return chunks