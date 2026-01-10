from typing import Iterator


def read_file_chunked(file_path: str, chunk_size: int = 100_000) -> Iterator[str]:
    """
    Read file in chunks.

    Args:
        file_path: Path to file
        chunk_size: Bytes to read at once (default 100KB)

    Yields:
        Text segments
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    except (UnicodeDecodeError, FileNotFoundError, PermissionError):
        return
