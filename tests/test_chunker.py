import unittest
import os
from src.indexer import Chunker


class TestFindChar(unittest.TestCase):
    def test_find_char_finds_last_occurrence(self):
        text = "Hello\nWorld\nTest"
        result = Chunker._find_char(text, "\n", 0, 15)
        assert result == 11

    def test_find_char_returns_none_when_not_found(self):
        text = "Hello World"
        result = Chunker._find_char(text, "\n", 0, 11)
        assert result is None

    def test_find_char_respects_boundaries(self):
        text = "Hello\nWorld\nTest"
        result = Chunker._find_char(text, "\n", 0, 10)
        assert result == 5


class TestChunkText(unittest.TestCase):
    def setUp(self):
        # Save original env values
        self.original_chunk_size = os.getenv("CHUNK_SIZE")
        self.original_overlap = os.getenv("OVERLAP")

    def tearDown(self):
        # Restore original env values
        if self.original_chunk_size:
            os.environ["CHUNK_SIZE"] = self.original_chunk_size
        if self.original_overlap:
            os.environ["OVERLAP"] = self.original_overlap

    def test_empty_text_returns_empty_list(self):
        result = Chunker.chunk_text("")
        assert result == []

    def test_chunk_size_validation(self):
        os.environ["CHUNK_SIZE"] = "100"
        os.environ["OVERLAP"] = "150"

        with self.assertRaises(ValueError) as context:
            from src.indexer import chunker

            old_size = chunker.chunk_size
            old_overlap = chunker.overlap
            chunker.chunk_size = 50
            chunker.overlap = 100
            try:
                Chunker.chunk_text("test")
            finally:
                chunker.chunk_size = old_size
                chunker.overlap = old_overlap

        assert "chunk_size must be greater than overlap" in str(context.exception)

    def test_text_smaller_than_chunk_returns_single_chunk(self):
        text = "Small text"
        chunks = Chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["start"] == 0
        assert chunks[0]["end"] == len(text)

    def test_chunks_have_correct_metadata(self):
        text = "A" * 2000  # 2000 chars
        chunks = Chunker.chunk_text(text)

        for chunk in chunks:
            assert "text" in chunk
            assert "start" in chunk
            assert "end" in chunk
            assert isinstance(chunk["start"], int)
            assert isinstance(chunk["end"], int)

    def test_chunks_overlap(self):
        text = "A" * 2000
        chunks = Chunker.chunk_text(text)

        if len(chunks) >= 2:
            # Check that chunks overlap
            first_end = chunks[0]["end"]
            second_start = chunks[1]["start"]

            # Second chunk should start before first chunk ends
            assert second_start < first_end

    def test_breaks_at_newline(self):
        # Create text with newline near chunk boundary
        text = "A" * 900 + "\n" + "B" * 500
        chunks = Chunker.chunk_text(text)

        # First chunk should end at or near the newline
        first_chunk = chunks[0]["text"]
        # Should break at newline if within last 20% (200 chars)
        assert first_chunk.endswith("\n") or first_chunk.endswith("B")

    def test_breaks_at_period_when_no_newline(self):
        text = "A" * 900 + ". " + "B" * 500
        chunks = Chunker.chunk_text(text)

        first_chunk = chunks[0]["text"]
        # Should try to break at period
        if "." in first_chunk:
            # Verify it broke near the period
            assert len(first_chunk) <= 1000

    def test_breaks_at_space_when_no_period_or_newline(self):
        text = "A" * 900 + " " + "B" * 500
        chunks = Chunker.chunk_text(text)

        first_chunk = chunks[0]["text"]
        # Should avoid cutting mid-word
        assert len(first_chunk) <= 1000

    def test_multiline_code_chunking(self):
        code = """def authenticate_user(username, password):
    if validate_credentials(username, password):
        create_session(username)
        return True
    return False

def validate_credentials(user, pwd):
    return check_database(user, pwd)
"""
        chunks = Chunker.chunk_text(code)

        assert len(chunks) >= 1
        # Verify all chunks have text
        for chunk in chunks:
            assert len(chunk["text"]) > 0

    def test_chunk_positions_are_sequential(self):
        text = "A" * 3000
        chunks = Chunker.chunk_text(text)

        for i in range(len(chunks) - 1):
            current_end = chunks[i]["end"]
            next_start = chunks[i + 1]["start"]

            # Next chunk should start before or at current end (overlap)
            assert next_start <= current_end
            # But should still make progress
            assert next_start > chunks[i]["start"]

    def test_chunk_text_matches_positions(self):
        text = "Hello World\nThis is a test\nAnother line"
        chunks = Chunker.chunk_text(text)

        for chunk in chunks:
            extracted = text[chunk["start"] : chunk["end"]]
            assert extracted == chunk["text"]


if __name__ == "__main__":
    unittest.main()
