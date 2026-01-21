import logging
import os
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from src.clients import MinIOClient, RedisClient
from src.models.pagination import PaginationParams, PaginatedResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from io import BytesIO
from src.cache import FileCache

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

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


@router.get("/", response_model=PaginatedResponse[dict])
@limiter.limit(f"{RATE_LIMIT_DOWNLOAD}/minute")
async def list_files(
    request: Request,
    prefix: str = "",
    pagination: PaginationParams = Depends()
):
    """
    List files in MinIO with pagination.

    Args:
        request: FastAPI request object (required for rate limiting)
        prefix: Optional prefix to filter files
        pagination: Pagination parameters (page, limit)

    Returns:
        Paginated list of files with metadata
    """
    try:
        redis = await RedisClient.get()
        file_cache = FileCache(redis)

        # Check cache for full file list
        files = await file_cache.get_files(prefix)

        if files is None:
            # Cache miss - fetch from MinIO
            files = MinIOClient.list_objects(prefix=prefix)
            await file_cache.cache_files(prefix, files)
            logger.info(f"Fetched and cached {len(files)} files with prefix '{prefix}'")

        # Paginate results
        total = len(files)
        start = pagination.offset
        end = start + pagination.limit
        paginated_files = files[start:end]

        return PaginatedResponse.create(
            items=paginated_files,
            total=total,
            page=pagination.page,
            limit=pagination.limit
        )

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
