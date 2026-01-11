"""Main FastAPI application entry point."""

import logging
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.routers import router, limiter
from src.utils.security import verify_api_key
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable must be set")

@asynccontextmanager
async def lifespan(app:FastAPI):
    """Initialize services on startup."""
    logger.info("Starting Semantic File Search API...")

    # Initialize clients
    from src.clients import QdrantClient, RedisClient, MinIOClient

    # Ensure MinIO bucket exists
    MinIOClient.ensure_bucket_exists()
    logger.info("MinIO bucket initialized")

    # Initialize Qdrant client
    await QdrantClient.init()
    await QdrantClient.ensure_collection_exists(COLLECTION_NAME)
    logger.info("Qdrant client initialized")

    # Initialize Redis client
    await RedisClient.init()
    logger.info("Redis client initialized")

    logger.info("API startup complete")

    yield


    """Cleanup on shutdown."""
    logger.info("Shutting down Semantic File Search API...")

    from src.clients import QdrantClient, RedisClient
    from src.embeddings import shutdown as shutdown_embeddings

    # Close connections
    await QdrantClient.close()
    await RedisClient.close()

    # Shutdown embedding thread pool
    shutdown_embeddings()

    logger.info("API shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Semantic File Search API",
    description="Semantic search for files using embeddings",
    version="0.1.0",
    lifespan=lifespan
)

COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "sfs-files")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Semantic File Search API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(router, dependencies=[Depends(verify_api_key)])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
