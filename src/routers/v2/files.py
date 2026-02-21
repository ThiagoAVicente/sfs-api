import logging
import os
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.cache import FileCache
from src.clients import MinIOClient, RedisClient
from src.models.pagination import PaginatedResponse, PaginationParams
from src.utils.validation import validate_collection_name, validate_filename

logger = logging.getLogger(__name__)
router = APIRouter()

# Import shared limiter
from src.routers import limiter

RATE_LIMIT_DOWNLOAD = os.environ.get("RATE_LIMIT_DOWNLOAD", "10")


@router.get("/{collection}/{file_name}")
@limiter.limit(f"{RATE_LIMIT_DOWNLOAD}/minute")
async def download_file(collection: str, file_name: str, request: Request):
    """
    Download a file from MinIO.

    Args:
        file_name: The name of the file to download
        request: FastAPI request object (required for rate limiting)

    Returns:
        File content as streaming response
    """
    try:
        # Validate collection name to prevent path traversal
        collection = validate_collection_name(collection)
        file_name = validate_filename(file_name)
        obs_name = f"{collection}/{file_name}"
        # Check if file exists
        if not MinIOClient.object_exists(obs_name):
            raise HTTPException(status_code=404, detail="File not found")

        # Download from MinIO
        file_data = MinIOClient.get_object(obs_name)

        if not file_data:
            raise HTTPException(status_code=500, detail="Failed to download file")

        logger.info(f"Downloaded file '{obs_name}'")

        # Return as streaming response
        return StreamingResponse(
            BytesIO(file_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
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
    collection: str = "",
    prefix: str = "",
    pagination: PaginationParams = Depends(),
):
    """
    List files in MinIO with pagination.

    Args:
        request: FastAPI request object (required for rate limiting)
        collection: Optional collection to filter files
        prefix: Optional additional prefix to filter files within collection
        pagination: Pagination parameters (page, limit)

    Returns:
        Paginated list of files with metadata
    """
    try:
        # Validate collection name if provided
        if collection:
            collection = validate_collection_name(collection)

        # Build the full prefix: collection/prefix or just prefix
        full_prefix = f"{collection}/{prefix}" if collection else prefix
        full_prefix = full_prefix.strip("/")

        redis = await RedisClient.get()
        file_cache = FileCache(redis)

        # Check cache
        files = await file_cache.get_files(full_prefix)

        if files is None:
            # Cache miss - fetch from MinIO (returns list of str paths)
            raw = MinIOClient.list_objects(prefix=full_prefix)
            # Convert each string path into a structured dict
            files = [
                {
                    "collection": p.split("/")[0] if "/" in p else "",
                    "name": p.split("/", 1)[1] if "/" in p else p,
                    "path": p,
                }
                for p in raw
            ]
            await file_cache.cache_files(full_prefix, files)
            logger.info(
                f"Fetched and cached {len(files)} files with prefix '{full_prefix}'"
            )

        # Paginate results
        total = len(files)
        start = pagination.offset
        end = start + pagination.limit
        paginated_files = files[start:end]

        return PaginatedResponse.create(
            items=paginated_files,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
        )

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
