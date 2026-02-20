"""Input validation utilities."""

import re
from fastapi import HTTPException

# Collection names must be alphanumeric, underscores, hyphens only
# Length: 1-64 characters
COLLECTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


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

    # Additional check: reject special cases
    if collection in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid collection name")

    return collection
