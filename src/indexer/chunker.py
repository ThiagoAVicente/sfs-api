import os

chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
overlap = int(os.getenv("OVERLAP", 200))

def _find_char(text:str, char:str, start:int, end:int) -> int|None:
    """
    Find last occurrence of char in text within limits

    Args:
        text (str): Text to search
        char (str): Character to find
        start (int): Start index
        end (int): End index
    Returns:
        int: Index of last occurrence or None if not found
    """

    val = text.rfind(char, start, end)
    return val if val != -1 else None

def chunk_text(text: str) -> list[dict[str, str | int]]:
    """
    Split text into overlapping chunks with smart boundaries.

    Args:
        text: Text to chunk

    Returns:
        List of dicts with 'text', 'start', 'end' keys
    """
    if not text:
        return []

    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks: list[dict[str, str | int]] = []
    start: int = 0
    text_size: int = len(text)
    increment: int = chunk_size - overlap
    natural_boundaries:tuple[str,...] = ("\n", ".", " ")

    # declarations for hints
    boundary:str
    natural_end:int | None

    while start < text_size:
        end: int = min(start + chunk_size, text_size)

        # Try to break at natural boundary
        if end < text_size and end > start:
            # Look for newline within last 20% of chunk
            boundary_search_start = max(start, end - int(chunk_size * 0.2))

            for boundary in natural_boundaries:
                natural_end = _find_char(text, boundary, boundary_search_start, end)

                if natural_end is None or natural_end <= start :
                    continue

                # stop at natural boundary instead
                end = natural_end +1
                break

        chunks.append({
            "text": text[start:end],
            "start": start,
            "end": end
        })

        start += increment

    return chunks
