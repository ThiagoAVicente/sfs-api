from src.embeddings import EmbeddingGenerator
from src.vector_store import QdrantClient


class Searcher:

    @classmethod
    async def search(
        cls,
        query: str,
        collection_name: str,
        limit: int = 5,
        score_threshold: float = 0.5
    ) -> list[dict]:
        """
        Search for similar documents.

        Args:
            query: Search query text
            collection_name: Name of the collection to search
            limit: Maximum number of results(min 1)
            score_threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of search results with score and payload
        """
        # Clip parameters to valid ranges
        score_threshold = max(0.0, min(1.0, score_threshold))
        limit = max(1, limit)

        # Generate embedding asynchronously
        query_embedding = await EmbeddingGenerator.embed_async(query)

        # flatten query
        query_embedding = query_embedding.flatten()

        # Search vector database
        return await QdrantClient.search(
            query_vector=query_embedding,
            collection_name=collection_name,
            limit=limit,
            score_threshold=score_threshold
        )
