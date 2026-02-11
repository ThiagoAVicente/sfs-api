import logging
from src.clients import QdrantClient, MinIOClient
import os
from .utils import clear_all_cache

logger = logging.getLogger(__name__)
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'default')

async def delete_file(ctx, file_path: str, *args, **kwargs) -> dict:
    """
    Delete a file from MinIO and its vectors from Qdrant.

    Args:
        ctx: arq context
        file_path: path to file in MinIO

    Returns:
        Status dict
    """
    try:
        logger.info(f"Deleting file: {file_path}")

        # Delete from MinIO
        MinIOClient.delete_object(file_path)

        await QdrantClient.delete_file(
            collection_name=COLLECTION_NAME,
            file_path=file_path
        )

        logger.info(f"Deleted {file_path}")
        return {"status": "complete", "file_path": file_path}

    except Exception as e:
        logger.error(f"Failed to delete: {e}")
        raise

    finally:
        await clear_all_cache()
