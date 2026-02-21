import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    FilterSelector,
    Filter,
    FieldCondition,
    MatchValue,
)
import hashlib
import numpy as np
import logging

logger = logging.getLogger(__name__)

host = os.environ.get("QDRANT_HOST", "localhost")
s_port: str = os.environ.get("QDRANT_PORT", "6333")
port: int
try:
    port = int(s_port)
except ValueError:
    raise ValueError("QDRANT_PORT must be an integer")


class QdrantClient:

    _client: AsyncQdrantClient | None = None

    @classmethod
    async def init(cls) -> AsyncQdrantClient:
        """Initialize global Qdrant client"""
        if cls._client is None:
            cls._client = AsyncQdrantClient(host=host, port=port)
            logger.info(f"Connected to Qdrant at {host}:{port}")
        return cls._client

    @classmethod
    async def close(cls):
        """Close Qdrant client"""
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
            logger.info("Qdrant connection closed")

    @classmethod
    async def get(cls) -> AsyncQdrantClient:
        """Get Qdrant client instance"""
        if cls._client is None:
            await cls.init()
        return cls._client

    @classmethod
    async def ensure_collection_exists(
        cls,
        collection_name: str,
        vector_size: int = 384,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """
        Create collection if it doesn't exist.

        Args:
            collection_name: Name of the collection
            vector_size: Embedding dimension
            distance: Distance metric
        Returns:
            True if collection exists or was created
        """
        client = await cls.get()

        # Check existing collections
        collections = await client.get_collections()
        existing_names = [c.name for c in collections.collections]

        if collection_name in existing_names:
            logger.info(f"Collection '{collection_name}' already exists")
            return True

        # Create new collection
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )
        logger.info(f"Created collection '{collection_name}'")
        return True

    @classmethod
    async def get_collections(cls) -> list[str]:
        client = await cls.get()
        collections = await client.get_collections()

        existing_names = [c.name for c in collections.collections]

        return existing_names

    @classmethod
    async def write(
        cls,
        vector: np.ndarray,
        collection_name: str,
        metadata: dict,
    ) -> bool:
        """
        Write vector + metadata to Qdrant collection.

        Args:
            vector: vector with data
            collection_name: Name of the collection
            metadata: Payload data (file_path, text, start, end, etc.)

        Returns:
            True if data was written successfully
        """

        client = await cls.get()

        # Generate ID
        file_path = metadata["file_path"]
        chunk_idx = metadata["chunk_index"]

        id_string = f"{file_path}:{chunk_idx}"
        point_id = int(
            hashlib.md5(id_string.encode(), usedforsecurity=False).hexdigest()[:16], 16
        )

        # Create point with vector + metadata
        point = PointStruct(id=point_id, vector=vector.tolist(), payload=metadata)

        # Write to Qdrant
        await client.upsert(collection_name=collection_name, points=[point])

        logger.info(f"Wrote point {point_id} to '{collection_name}'")
        return True

    @classmethod
    async def delete_file(cls, collection_name: str, file_path: str):
        """
        Remove all vectors related to a file
        Args:
            file_path: Path to file
        """
        client = await cls.get()
        filter: Filter = Filter(
            must=[FieldCondition(key="file_path", match=MatchValue(value=file_path))]
        )
        points_selector: FilterSelector = FilterSelector(filter=filter)

        await client.delete(
            collection_name=collection_name, points_selector=points_selector
        )

    @classmethod
    async def search(
        cls,
        query_vector: np.ndarray,
        collection_name: str,
        limit: int = 5,
        score_threshold: float | None = None,
    ) -> list[dict]:
        """
        Search for similar vectors in collection.

        Args:
            query_vector: Query embedding
            collection_name: Collection to search
            limit: Max results to return
            score_threshold: Min similarity score

        Returns:
            List of dicts:
        """
        client = await cls.get()

        result = await client.query_points(
            collection_name=collection_name,
            query=query_vector.tolist(),
            limit=limit,
            score_threshold=score_threshold,
        )

        # Convert to dict format
        return [
            {"score": point.score, "payload": point.payload} for point in result.points
        ]
