import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from .model import get_model
import numpy as np

_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    """Get or create the shared thread pool for embeddings."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=os.cpu_count(),
            thread_name_prefix="embedding"
        )
    return _executor


def shutdown() -> None:
    """Shutdown the embedding thread pool. Call on application shutdown."""
    global _executor
    if _executor:
        _executor.shutdown(wait=True)
        _executor = None


class EmbeddingGenerator:
    """Generate embeddings with async support via thread pool."""

    @staticmethod
    def embed(texts: list[str] | str) -> np.ndarray:
        """
        Generate embeddings for texts. Synchronous - blocks caller.

        Args:
            texts: A text string or list of text strings.

        Returns:
            np.ndarray: An array of embeddings

        Raises:
            ValueError: If input is empty.
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            raise ValueError("Input is empty")

        model = get_model()
        return model.encode(texts)

    @staticmethod
    async def embed_async(texts: list[str] | str) -> np.ndarray:
        """
        Generate embeddings asynchronously. Runs in thread pool, doesn't block event loop.

        Args:
            texts: A text string or list of text strings.

        Returns:
            np.ndarray: An array of embeddings
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_get_executor(), EmbeddingGenerator.embed, texts)
