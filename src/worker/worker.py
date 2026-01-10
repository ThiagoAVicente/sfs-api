import logging
from arq import run_worker
from arq.typing import WorkerSettingsBase
from src.worker.flows import IndexFileFlow, DeleteFileFlow

logger = logging.getLogger(__name__)


async def startup(ctx):
    """Initialize worker on startup."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("Worker starting up...")

    # Initialize clients
    from src.clients import MinIOClient, QdrantClient

    # Ensure MinIO bucket exists
    MinIOClient.ensure_bucket_exists()

    # Initialize Qdrant client
    await QdrantClient.init()


async def shutdown(ctx):
    """Clean up on shutdown."""
    logger.info("Worker shutting down...")
    from src.clients import QdrantClient
    await QdrantClient.close()


class WorkerSettings(WorkerSettingsBase):
    """arq worker settings."""

    functions = [
        IndexFileFlow.index_file,
        DeleteFileFlow.delete_file
    ]

    on_startup = startup
    on_shutdown = shutdown

def run():
    run_worker(WorkerSettings)
