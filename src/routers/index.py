import logging
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form
from src.clients import RedisClient, MinIOClient
from src.models import StatusResponse, JobRequest
from src.utils import required
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.utils.support import FileType

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

RATE_LIMIT_UPLOAD = os.environ.get('RATE_LIMIT_UPLOAD', '10')
RATE_LIMIT_DELETE = os.environ.get('RATE_LIMIT_DELETE', '10')
RATE_LIMIT_STATUS = os.environ.get('RATE_LIMIT_STATUS', '100')
MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', '50'))


@router.post("")
@limiter.limit(f"{RATE_LIMIT_UPLOAD}/minute")
async def index_file(
    request: Request,
    file: UploadFile = File(...),
    update: bool = Form(False)
):
    """
    Upload a file and enqueue it for indexing.

    Returns:
        job_id: Use this to check indexing status
    """
    try:

        required(file, "file")

        required(file.filename, "filename")
        file_name:str = file.filename

        required(file.content_type, "content type")
        content_type:str= file.content_type

        # Read file content
        content = await file.read()

        # Check file size (in bytes)
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB, got {file_size_mb:.2f}MB"
            )

        file_support_response = FileType.is_supported(content)
        if not file_support_response.val:
            raise HTTPException(
                status_code=415,
                detail=f"Rejected file [{file_support_response.explanation}]"
            )
        file_type = file_support_response.type

        # check if file exists on minio
        if MinIOClient.object_exists(file_name):
            if not update:
                raise HTTPException(status_code=400, detail="File already exists, use update=True if you want to update the file")
            logger.debug(f"File '{file_name}' already exists, updating...")

        # Upload to MinIO
        success = MinIOClient.put_object(
            object_name=file_name,
            data=content,
            content_type=content_type
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload file")

        logger.info(f"Uploaded file '{file.filename}'")

        # Enqueue indexing job
        request = JobRequest(function='index_file', file_name=file_name, file_type=file_type)
        job_id = await RedisClient.enqueue_job(request)

        return {"job_id": job_id}

    except HTTPException as exc:
        logger.error(f"Error indexing file: {exc}")
        raise exc

    except Exception as e:
        logger.error(f"Error indexing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=StatusResponse)
@limiter.limit(f"{RATE_LIMIT_STATUS}/minute")
async def get_status(request: Request, job_id: str):
    """
    Check the status of an indexing job.

    Args:
        job_id: The job ID returned from /index

    Returns:
        Job status (queued, in_progress, complete, failed)
    """
    try:
        status = await RedisClient.get_job_status(job_id)

        if status is None:
            raise HTTPException(status_code=404, detail="Job not found")

        return StatusResponse(job_id=job_id, status=status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_name}")
@limiter.limit(f"{RATE_LIMIT_DELETE}/minute")
async def delete_file(request: Request, file_name: str):
    """
    Delete a file from the index.

    Args:
        file_name: The name of the file to delete

    Returns:
        job id
    """
    try:
        request = JobRequest(function='delete_file', file_name=file_name)
        job_id = await RedisClient.enqueue_job(request)
        return {"job_id": job_id}

    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
