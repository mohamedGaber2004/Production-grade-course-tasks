"""Metadata enrichment adapter implementing the domain service."""

from typing import List
from domain.entities import Chunk
from domain.services import MetadataEnrichmentService
from infrastructure.adapters.metadata import MetadataEnricher


class ProductionMetadataAdapter(MetadataEnrichmentService):
    """Adapter for metadata enrichment."""

    def __init__(self, enricher: MetadataEnricher):
        self.enricher = enricher

    def enrich_metadata(self, chunks: List[Chunk]) -> List[Chunk]:
        """Enrich chunks with metadata."""
        # Convert to format expected by enricher
        chunk_dicts = [
            {
                'content': chunk.content,
                'metadata': chunk.metadata,
            }
            for chunk in chunks
        ]
        enriched = self.enricher.enrich_batch(chunk_dicts)

        # Convert back to domain chunks
        enriched_chunks = []
        for i, enriched_dict in enumerate(enriched):
            chunk = chunks[i]
            chunk.metadata.update(enriched_dict['metadata'])
            enriched_chunks.append(chunk)
        return enriched_chunks