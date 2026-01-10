"""
Integration tests for Searcher using testcontainers.
"""

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy


@pytest.fixture(scope="class")
def qdrant_container():
    """Start Qdrant container for tests."""
    container = DockerContainer("qdrant/qdrant:latest")
    container.with_exposed_ports(6333)
    container.waiting_for(HttpWaitStrategy(6333).for_status_code(200))
    container.start()
    yield container
    container.stop()


@pytest.fixture(autouse=True)
async def setup(qdrant_container):
    """Setup client with testcontainer."""
    import os
    from src.vector_store import QdrantClient

    QdrantClient._client = None

    host = qdrant_container.get_container_host_ip()
    port = qdrant_container.get_exposed_port(6333)

    os.environ["QDRANT_HOST"] = host
    os.environ["QDRANT_PORT"] = str(port)

    import importlib
    import src.vector_store.qdrant_client as qc_module
    importlib.reload(qc_module)

    yield

    await QdrantClient.close()
    QdrantClient._client = None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_end_to_end():
    """Test full search flow."""
    from src.search.searcher import Searcher
    from src.vector_store import QdrantClient
    from src.embeddings import EmbeddingGenerator

    collection_name = "test_collection"

    await QdrantClient.ensure_collection_exists(
        collection_name=collection_name,
        vector_size=384
    )

    # Insert test documents
    docs = [
        "Python is a programming language",
        "JavaScript is used for web development",
        "Machine learning uses neural networks"
    ]

    embeddings = EmbeddingGenerator.embed(docs)

    for i, (text, embedding) in enumerate(zip(docs, embeddings)):
        await QdrantClient.write(
            vector=embedding,
            collection_name=collection_name,
            metadata={"text": text, "chunk_index": i, "file_path": f"/file{i}.py"}
        )

    # Search
    results = await Searcher.search(
        query="programming code",
        collection_name=collection_name,
        limit=3
    )

    assert len(results) > 0
    assert "score" in results[0]
    assert "payload" in results[0]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_with_threshold():
    """Test search filters by score threshold."""
    from src.search.searcher import Searcher
    from src.vector_store import QdrantClient
    from src.embeddings import EmbeddingGenerator

    collection_name = "test_threshold"

    await QdrantClient.ensure_collection_exists(
        collection_name=collection_name,
        vector_size=384
    )

    docs = [
        "artificial intelligence and machine learning",
        "cooking recipes and food preparation"
    ]

    embeddings = EmbeddingGenerator.embed(docs)

    for i, (text, embedding) in enumerate(zip(docs, embeddings)):
        await QdrantClient.write(
            vector=embedding,
            collection_name=collection_name,
            metadata={"text": text, "chunk_index": i, "file_path": f"/doc{i}.txt"}
        )

    results = await Searcher.search(
        query="AI and neural networks",
        collection_name=collection_name,
        limit=10,
        score_threshold=0.6
    )

    for result in results:
        assert result["score"] >= 0.6


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_clips_invalid_params():
    """Test that invalid params are clipped to valid ranges."""
    from src.search.searcher import Searcher
    from src.vector_store import QdrantClient
    from src.embeddings import EmbeddingGenerator

    collection_name = "test_params"

    await QdrantClient.ensure_collection_exists(
        collection_name=collection_name,
        vector_size=384
    )

    EmbeddingGenerator.embed(["test"])

    # These should not raise errors
    await Searcher.search(
        query="test",
        collection_name=collection_name,
        limit=-5,  # Should be clipped to 1
        score_threshold=2.0  # Should be clipped to 1.0
    )

    await Searcher.search(
        query="test",
        collection_name=collection_name,
        score_threshold=-1.0  # Should be clipped to 0.0
    )
