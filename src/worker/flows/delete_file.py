import logging
from src.clients import QdrantClient, MinIOClient
import os
from .utils import clear_all_cache

logger = logging.getLogger(__name__)


async def delete_file(ctx, collection: str, file_path: str, *args, **kwargs) -> dict:
    """
    Delete a file from MinIO and its vectors from Qdrant.

    Args:
        ctx: arq context
        collection: collection where file is
        file_path: path to file in MinIO

    Returns:
        Status dict
    """
    try:
        logger.info(f"Deleting file: {file_path} from collection: {collection}")

        # Delete from MinIO
        MinIOClient.delete_object(f"{collection}/{file_path}")

        await QdrantClient.delete_file(collection_name=collection, file_path=file_path)

        logger.info(f"Deleted {file_path} from {collection}")
        return {"status": "complete", "file_path": file_path}

    except Exception as e:
        logger.error(f"Failed to delete: {e}")
        raise

    finally:
        await clear_all_cache()
