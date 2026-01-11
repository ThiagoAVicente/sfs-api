from src.indexer import Chunker
from src.embeddings import EmbeddingGenerator
from src.clients import QdrantClient, MinIOClient
import logging
import os

logger = logging.getLogger(__name__)
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'default')

class IndexFileFlow:
    """
    Flow to add/update embeddings of a file
    """
    @staticmethod
    async def index_file(ctx, file_path:str) -> dict:
        """
        Index a file
        Args:
            ctx: arq context
            file_path: path to file on minio

        Returns:
            Status dict with results
        """
        try:
            # get file from minio
            file_data = MinIOClient.get_object(file_path)
            if not file_data:
                raise Exception(f"Failed to download {file_path}")

            # chunk file
            text = file_data.decode('utf-8')
            chunks = Chunker.chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks")

            # generate embeddings
            chunk_texts = [c['text'] for c in chunks]
            embeddings = await EmbeddingGenerator.embed_async(chunk_texts)

            # store in qdrant
            for i, (chunk,embedding) in enumerate(zip(chunks, embeddings)):

                metadata = {
                    "file_path": file_path,
                    "text": chunk['text'],
                    "start": chunk['start'],
                    "end": chunk['end'],
                    "chunk_index": i,
                }

                await QdrantClient.write(
                    collection_name=COLLECTION_NAME,
                    vector=embedding,
                    metadata=metadata
                )

            logger.info(f"Indexed {len(chunks)} chunks")
            return {"status": "complete", "chunks_indexed": len(chunks)}

        except Exception as e:
            logger.error(f"Failed: {e}")
            raise
