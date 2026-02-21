"""Tests for FileAbstraction."""

import pytest
from src.utils import FileAbstraction


class TestFileAbstraction:
    """Tests for FileAbstraction class."""

    def test_get_text_from_text_file(self):
        """Test extracting text from a text file."""
        file_data = b"Hello, world!\nThis is a test."
        result = FileAbstraction.get_text(file_data, "text")
        assert result == "Hello, world!\nThis is a test."

    def test_get_text_from_text_file_with_utf8(self):
        """Test extracting text from UTF-8 encoded text file."""
        file_data = "Hello, 世界! 🌍".encode("utf-8")
        result = FileAbstraction.get_text(file_data, "text")
        assert result == "Hello, 世界! 🌍"

    def test_get_text_from_text_file_with_invalid_utf8(self):
        """Test extracting text from text file with invalid UTF-8 uses replacement."""
        file_data = b"Hello\xfe\xffWorld"
        result = FileAbstraction.get_text(file_data, "text")
        # Should replace invalid bytes with replacement character
        assert "Hello" in result
        assert "World" in result

    def test_get_text_from_unsupported_file_type(self):
        """Test that unsupported file types raise ValueError."""
        file_data = b"some data"
        with pytest.raises(ValueError) as exc_info:
            FileAbstraction.get_text(file_data, "docx")
        assert "Unsupported file type" in str(exc_info.value)

    def test_pdf_to_text_simple_pdf(self):
        """Test extracting text from a simple PDF."""
        # Minimal valid PDF
        pdf_data = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000202 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        result = FileAbstraction.get_text(pdf_data, "pdf")
        # Should extract some text (even if minimal)
        assert isinstance(result, str)

    def test_pdf_to_text_invalid_pdf_returns_empty(self):
        """Test that truncated PDF raises ValueError."""
        pdf_data = b"%PDF-1.4%%EOF"
        with pytest.raises(ValueError) as exc_info:
            FileAbstraction.get_text(pdf_data, "pdf")
        assert "Malformed PDF" in str(exc_info.value)

    def test_pdf_to_text_malformed_pdf(self):
        """Test that malformed PDF raises an appropriate error."""
        # Not a valid PDF
        pdf_data = b"This is not a PDF"
        with pytest.raises(Exception):
            FileAbstraction.get_text(pdf_data, "pdf")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
