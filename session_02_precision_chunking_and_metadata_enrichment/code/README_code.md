# Session 2 — Precision Chunking & Metadata Enrichment

> **Stack:** Gemini 2.0 Flash · Voyage AI · Qdrant · FastAPI · Docker

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Client (Postman / curl)                   │
└──────────┬───────────────────────────────────────────────────┘
           │ HTTP
┌──────────▼───────────────────────────────────────────────────┐
│                  FastAPI Application (port 8000)              │
│                                                               │
│  ┌──────────┐  ┌─────────────────────────────────────────┐   │
│  │ Ingest   │  │ Chat Router                             │   │
│  │ (PDF +   │  │ • content_type_filter (optional)        │   │
│  │ enrich)  │  │ • Returns CRAG verdict + citations      │   │
│  └────┬─────┘  └────┬────────────────────────────────────┘   │
│       │              │                                        │
│  ┌────▼──────────────▼───────────────────────────────────┐   │
│  │                  RAG Service                           │   │
│  │                                                        │   │
│  │  PDF → Chunk ──→ Metadata Enrich ──→ Index             │   │
│  │        (3 strategies)  (LLM-powered)                   │   │
│  │                                                        │   │
│  │  Query → Filtered Retrieve → CRAG Evaluate ──→ {       │   │
│  │    CORRECT   → Rerank → Grounded Generate              │   │
│  │    AMBIGUOUS → Refine Query → Re-retrieve → Generate   │   │
│  │    INCORRECT → Refuse (no hallucination)               │   │
│  │  }                                                     │   │
│  └──────┬───────────┬───────────────────┬─────────────────┘   │
│         │           │                   │                     │
│  ┌──────▼──────┐ ┌──▼───────────┐ ┌────▼─────────────────┐   │
│  │ Chunking    │ │ Metadata     │ │ CRAG Evaluator       │   │
│  │ • Fixed     │ │ Enricher     │ │ • Verdict scoring    │   │
│  │ • Recursive │ │ (Gemini)     │ │ • Query refinement   │   │
│  │ • Semantic  │ │              │ │                      │   │
│  └─────────────┘ └──────────────┘ └──────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│          Qdrant (port 6333) — Filtered Search                 │
│          Payload filters by content_type, topic, entities     │
└──────────────────────────────────────────────────────────────┘
```

---

## What's New vs Session 1

| Feature          | Session 1              | Session 2                                                 |
| ---------------- | ---------------------- | --------------------------------------------------------- |
| Chunking         | Fixed + Recursive      | + **Semantic** (embedding-based sentence grouping)        |
| Metadata         | Page number only       | **LLM-extracted**: topic, content_type, entities, summary |
| Retrieval        | Vector similarity only | + **Qdrant payload filters** (pre-retrieval narrowing)    |
| Self-evaluation  | None                   | **CRAG** (Correct / Ambiguous / Incorrect)                |
| Error handling   | Generic 500            | CRAG refuses bad retrievals → **zero hallucination**      |
| Query refinement | None                   | Automatic query rewrite on ambiguous results              |

---

## Quick Start

### 1. Configure

```bash
cd production
cp .env.example .env
# Add GEMINI_API_KEY and VOYAGE_API_KEY
```

### 2. Start

```bash
# Full stack
docker compose up --build -d

# OR local dev
docker compose up qdrant -d
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Ingest (with LLM metadata enrichment)

```bash
curl -X POST http://localhost:8000/api/v1/ingest?enrich=true \
  -F "file=@/path/to/document.pdf"
```

### 4. Query (with CRAG + optional filter)

```bash
# Unfiltered
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What methodology is used?"}'

# Filtered by content type
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the results?", "content_type_filter": "results"}'
```

**Response includes:**

```json
{
  "answer": "...",
  "sources": [
    { "ref": "[1]", "page": 5, "content_type": "results", "topic": "..." }
  ],
  "verdict": "CORRECT",
  "refined_query": null,
  "attempts": 1
}
```

---

## Postman Setup

1. **Import** `postman/rag_api.postman_collection.json`
2. Set `base_url` → `http://localhost:8000`
3. Test: Health → Ingest PDF → Query (unfiltered) → Query (filtered) → Query (unrelated, triggers INCORRECT)

---

## File Structure

```
production/
├── main.py                           # FastAPI entry point (CRAG status in health)
├── config.py                         # Chunking strategy + CRAG toggle
├── dependencies.py                   # DI with strategy selection
├── middleware.py                     # X-Request-ID + latency
├── Dockerfile / docker-compose.yml
├── .env.example
│
├── routers/
│   ├── chat.py                       # POST /api/v1/chat (content_type_filter + verdict)
│   └── ingest.py                     # POST /api/v1/ingest?enrich=true|false
│
├── services/
│   ├── chunking.py                   # Fixed + Recursive + Semantic (embedding-based)
│   ├── metadata.py                   # LLM-powered structured extraction
│   ├── crag.py                       # Corrective RAG evaluator
│   └── rag_service.py                # Full pipeline with CRAG integration
│
├── database/
│   └── vector_store.py               # Qdrant + filtered_search()
│
├── tests/
│   ├── unit/test_chunking.py         # All 3 strategies + semantic mock
│   ├── unit/test_crag.py             # Verdict parsing tests
│   ├── integration/test_api.py       # Full API + CRAG + filter tests
│   ├── load/k6_smoke.js             # Smoke + load + filtered scenarios
│   └── requirements-test.txt
│
├── postman/rag_api.postman_collection.json
├── monitoring/prometheus.yml
└── .github/workflows/ci.yml
```

---

## Testing

```bash
# Unit tests (no API keys)
pytest tests/unit/ -v

# Integration tests (Qdrant + API keys)
docker compose up qdrant -d
pytest tests/integration/ -v

# k6 load test
k6 run tests/load/k6_smoke.js

# Docker k6
docker compose --profile testing up k6
```

---

## Configuration

| Variable                      | Default     | Description                             |
| ----------------------------- | ----------- | --------------------------------------- |
| `CHUNKING_STRATEGY`           | `recursive` | `fixed`, `recursive`, or `semantic`     |
| `CHUNKING_SEMANTIC_THRESHOLD` | `0.72`      | Cosine similarity for semantic grouping |
| `RETRIEVER_ENABLE_CRAG`       | `true`      | Enable/disable Corrective RAG           |
| `RETRIEVER_INITIAL_K`         | `10`        | Over-retrieval count                    |
| `RETRIEVER_RERANK_TOP_K`      | `3`         | Final sources after reranking           |

---

## Production Patterns Demonstrated

| Pattern                 | Location                   | Why                                        |
| ----------------------- | -------------------------- | ------------------------------------------ |
| Semantic Chunking       | `services/chunking.py`     | Embedding-based coherent segments          |
| LLM Metadata Extraction | `services/metadata.py`     | Structured fields for filtered retrieval   |
| Payload-Filtered Search | `database/vector_store.py` | Narrow search space before similarity      |
| CRAG (Corrective RAG)   | `services/crag.py`         | Self-evaluating pipeline, no hallucination |
| Query Refinement        | `services/crag.py`         | Auto-rewrite ambiguous queries             |
| Source Traceability     | `routers/chat.py`          | Numbered citations with page + type        |
| Strategy Pattern        | `services/chunking.py`     | Swap chunking via env var                  |
| Feature Toggle          | `config.py`                | CRAG on/off without code changes           |

---

## Research Notebooks

| Notebook                                 | Topics                                                                                   |
| ---------------------------------------- | ---------------------------------------------------------------------------------------- |
| `01_chunking_strategies_deep_dive.ipynb` | Fixed vs Recursive vs Semantic, chunk quality analysis, retrieval benchmark              |
| `02_metadata_enrichment_and_crag.ipynb`  | LLM metadata extraction, Qdrant filtered search, source traceability, full CRAG pipeline |
