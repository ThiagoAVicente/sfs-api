import logging
from src.clients import QdrantClient, MinIOClient
import os

logger = logging.getLogger(__name__)
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'default')


class DeleteFileFlow:
    """Flow to delete a file from vector store and MinIO."""

    @staticmethod
    async def delete_file(ctx, file_path: str, job_id: str) -> dict:
        """
        Delete a file from MinIO and its vectors from Qdrant.

        Args:
            ctx: arq context
            file_path: path to file in MinIO
            job_id: job id for tracking

        Returns:
            Status dict
        """
        try:
            logger.info(f"[{job_id}] Deleting file: {file_path}")

            # Delete from MinIO
            MinIOClient.delete_object(file_path)

            await QdrantClient.delete_file(
                collection_name=COLLECTION_NAME,
                file_path=file_path
            )

            logger.info(f"[{job_id}] Deleted {file_path}")
            return {"status": "complete", "file_path": file_path}

        except Exception as e:
            logger.error(f"[{job_id}] Failed to delete: {e}")
            raise
