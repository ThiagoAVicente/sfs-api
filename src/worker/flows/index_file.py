from src.indexer import Chunker
from src.embeddings import EmbeddingGenerator
from src.clients import QdrantClient, MinIOClient
from src.utils import FileAbstraction
import logging
import re
from .utils import clear_all_cache

logger = logging.getLogger(__name__)


async def index_file(
    ctx, collection: str, file_path: str, file_type: str, *args, **kwargs
) -> dict:
    """
    Index a file
    Args:
        ctx: arq context
        collection: collection where to save file
        file_path: path to file on minio
        file_type: file type

    Returns:
        Status dict with results
    """
    try:
        # get file from minio
        file_data = MinIOClient.get_object(f"{collection}/{file_path}")
        if not file_data:
            raise Exception(f"Failed to download {file_path}")

        # chunk file
        text = FileAbstraction.get_text(file_data, file_type)
        text = re.sub(r"\s+", " ", text).strip()

        chunks = Chunker.chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")

        # generate embeddings
        chunk_texts = [c["text"] for c in chunks]
        embeddings = await EmbeddingGenerator.embed_async(chunk_texts)

        await QdrantClient.ensure_collection_exists(collection_name=collection)

        # store in qdrant
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):

            metadata = {
                "file_path": file_path,
                "text": chunk["text"],
                "start": chunk["start"],
                "end": chunk["end"],
                "chunk_index": i,
            }

            await QdrantClient.write(
                collection_name=collection, vector=embedding, metadata=metadata
            )

        logger.info(f"Indexed {len(chunks)} chunks")
        return {"status": "complete", "chunks_indexed": len(chunks)}

    except Exception as e:
        logger.error(f"Failed: {e}")
        raise

    finally:
        await clear_all_cache()
