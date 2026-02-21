"""Input validation utilities."""

import re

from fastapi import HTTPException

# Collection names: alphanumeric, underscores, hyphens only (no dots, slashes)
COLLECTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# File names: alphanumeric, underscores, hyphens, dots (for extensions)
# No slashes, no backslashes, no path traversal
FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,255}$")


def validate_collection_name(collection: str) -> str:
    """
    Validate collection name to prevent path traversal and injection attacks.

    Args:
        collection: User-supplied collection name

    Returns:
        The validated collection name (unchanged if valid)

    Raises:
        HTTPException(400): If collection name is invalid
    """
    if not collection:
        raise HTTPException(status_code=400, detail="Collection name cannot be empty")

    if not COLLECTION_NAME_PATTERN.match(collection):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid collection name. Must be 1-64 characters "
                "and contain only letters, numbers, underscores, and hyphens."
            ),
        )

    # Reject special cases
    if collection in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid collection name")

    return collection


def validate_filename(filename: str) -> str:
    """
    Validate filename to prevent path traversal attacks.

    Args:
        filename: User-supplied filename

    Returns:
        The validated filename (unchanged if valid)

    Raises:
        HTTPException(400): If filename is invalid
    """
    if not filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    if not FILENAME_PATTERN.match(filename):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid filename. Must be 1-255 characters and contain only "
                "letters, numbers, underscores, hyphens, and dots. "
                "No slashes or path separators allowed."
            ),
        )

    # Reject path traversal attempts
    if filename in (".", "..") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    return filename
