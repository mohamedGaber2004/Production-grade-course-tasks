"""Session 2 — Precision Chunking & Metadata Enrichment API with Hexagonal Architecture."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.infrastructure.config.config import get_settings
from src.infrastructure.middleware.middleware import RequestIDMiddleware
from src.infrastructure.config.dependencies import get_vector_store
from src.presentation.api import chat, ingest, compare, debug
from src.infrastructure.adapters.metrics import get_metrics, get_content_type  # Assuming metrics is moved

structlog.configure(
    processors=[structlog.contextvars.merge_contextvars, structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer() if get_settings().debug else structlog.processors.JSONRenderer()],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    logger.info("starting", app=s.app_name, version=s.version, chunking=s.chunking.strategy,
                crag=s.retriever.enable_crag, enrichment=s.retriever.enrichment_mode)
    vs = get_vector_store()
    if not vs.health_check():
        raise RuntimeError(f"Qdrant unreachable at {s.qdrant.url}")
    logger.info("ready")
    yield
    logger.info("shutdown")

app = FastAPI(
    title="Precision Chunking & CRAG API (Hexagonal)",
    description="Session 2: Semantic chunking, metadata enrichment, filtered retrieval, CRAG, strategy comparison - Hexagonal Architecture",
    version="2.0.0", lifespan=lifespan,
)
app.add_middleware(RequestIDMiddleware)
app.include_router(chat.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(compare.router, prefix="/api/v1")
app.include_router(debug.router, prefix="/api/v1")

@app.get("/health", tags=["System"])
def health():
    s = get_settings()
    return {
        "status": "healthy", "qdrant": get_vector_store().is_ready, "version": "2.0.0",
        "chunking_strategy": s.chunking.strategy, "crag_enabled": s.retriever.enable_crag,
        "enrichment_mode": s.retriever.enrichment_mode,
    }