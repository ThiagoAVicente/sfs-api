import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from src.utils import FileType

class TestFileType:
    def test_is_supported(self):
        # Test with supported file content
        file_content = b'Hello, world!'
        assert FileType.is_supported(file_content).val == True

        # Test with unsupported file content
        file_content = b'\x00\x01\x02\x03'
        assert FileType.is_supported(file_content).val == False

        # Test with allowed non-text file content (PDF)
        file_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF'
        assert FileType.is_supported(file_content).val == True
