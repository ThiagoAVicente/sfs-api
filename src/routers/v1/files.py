import logging
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from src.clients import MinIOClient, RedisClient
from io import BytesIO
from src.cache import FileCache

logger = logging.getLogger(__name__)
router = APIRouter()

# Import shared limiter
from src.routers import limiter

RATE_LIMIT_DOWNLOAD = os.environ.get('RATE_LIMIT_DOWNLOAD', '10')


@router.get("/{file_name}")
@limiter.limit(f"{RATE_LIMIT_DOWNLOAD}/minute")
async def download_file(file_name: str, request: Request):
    """
    Download a file from MinIO.

    Args:
        file_name: The name of the file to download
        request: FastAPI request object (required for rate limiting)

    Returns:
        File content as streaming response
    """
    try:
        # Check if file exists
        if not MinIOClient.object_exists(file_name):
            raise HTTPException(status_code=404, detail="File not found")

        # Download from MinIO
        file_data = MinIOClient.get_object(file_name)

        if not file_data:
            raise HTTPException(status_code=500, detail="Failed to download file")

        logger.info(f"Downloaded file '{file_name}'")

        # Return as streaming response
        return StreamingResponse(
            BytesIO(file_data),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
@limiter.limit(f"{RATE_LIMIT_DOWNLOAD}/minute")
async def list_files(request: Request, prefix: str = ""):
    """
    List all files in MinIO.

    Args:
        request: FastAPI request object (required for rate limiting)
        prefix: Optional prefix to filter files

    Returns:
        List of file names
    """

    redis = await RedisClient.get()
    file_cache = FileCache(redis)

    # check for hits on cache
    files = await file_cache.get_files(prefix)
    if files is not None:
        return {"files": files, "count": len(files)}

    try:
        files = MinIOClient.list_objects(prefix=prefix)
        await file_cache.cache_files(prefix, files)
        return {"files": files, "count": len(files)}

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
