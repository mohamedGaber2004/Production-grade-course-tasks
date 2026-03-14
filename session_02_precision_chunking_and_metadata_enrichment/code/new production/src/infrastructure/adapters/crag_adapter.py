"""CRAG evaluator adapter implementing the domain service."""

from typing import List
from domain.entities import Chunk
from domain.services import CRAGEvaluatorService
from infrastructure.adapters.crag import CRAGEvaluator


class CRAGAdapter(CRAGEvaluatorService):
    """Adapter for CRAG evaluation."""

    def __init__(self, evaluator: CRAGEvaluator):
        self.evaluator = evaluator

    def evaluate_and_rerank(self, query: str, chunks: List[Chunk]) -> List[Chunk]:
        """Evaluate and rerank chunks using CRAG."""
        # Convert to format expected by evaluator
        chunk_dicts = [
            {
                'content': chunk.content,
                'metadata': chunk.metadata,
            }
            for chunk in chunks
        ]
        reranked = self.evaluator.evaluate_and_rerank(query, chunk_dicts)

        # Convert back to domain chunks
        reranked_chunks = []
        for reranked_dict in reranked:
            # Find the original chunk
            original_chunk = next(
                (c for c in chunks if c.content == reranked_dict['content']),
                None
            )
            if original_chunk:
                # Update metadata with CRAG score
                original_chunk.metadata['crag_score'] = reranked_dict.get('score', 0)
                reranked_chunks.append(original_chunk)
        return reranked_chunks