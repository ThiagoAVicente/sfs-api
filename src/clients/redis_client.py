"""Redis client for arq task queue and job status tracking."""

import os
import logging
from arq import create_pool, ArqRedis
from arq.jobs import Job
from arq.connections import RedisSettings

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


class RedisClient:
    """Redis client wrapper with singleton pattern for arq jobs."""

    _pool = None

    @classmethod
    async def init(cls):
        """Initialize global Redis pool."""
        if cls._pool is None:
            settings = RedisSettings(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
            )
            cls._pool = await create_pool(settings)
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return cls._pool

    @classmethod
    async def close(cls):
        """Close Redis pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
            logger.info("Redis connection closed")

    @classmethod
    async def get(cls) -> ArqRedis:
        """Get Redis pool instance."""
        if cls._pool is None:
            await cls.init()
        return cls._pool

    @classmethod
    async def enqueue_job(cls, function_name: str, file_path: str) -> str:
        """
        Enqueue a job to be processed by the worker.

        Args:
            function_name: Name of the worker function to run
            file_path: Path to the file in MinIO

        Returns:
            The job ID
        """
        pool = await cls.get()
        job = await pool.enqueue_job(function_name, file_path=file_path)
        if job is None:
            raise ValueError(f"Failed to enqueue job for '{file_path}'")

        logger.info(f"Enqueued job {job.job_id} for '{file_path}'")
        return job.job_id

    @classmethod
    async def get_job_status(cls, job_id: str) -> str:
        """
        Get the status of a job.

        Args:
            job_id: The job ID to check

        Returns:
            Job status or None
        """
        pool = await cls.get()
        job = Job(
            job_id=job_id,
            redis=pool
        )
        return await job.status()
