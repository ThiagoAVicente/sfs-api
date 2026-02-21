"""Tests for input validation utilities."""

import pytest
from fastapi import HTTPException

from src.utils.validation import validate_collection_name, validate_filename


class TestCollectionNameValidation:
    """Tests for collection name validation."""

    def test_valid_alphanumeric(self):
        """Test valid alphanumeric collection names."""
        assert validate_collection_name("default") == "default"
        assert validate_collection_name("collection123") == "collection123"
        assert validate_collection_name("MyCollection") == "MyCollection"

    def test_valid_with_underscore_hyphen(self):
        """Test valid names with underscores and hyphens."""
        assert validate_collection_name("my_collection") == "my_collection"
        assert validate_collection_name("my-collection") == "my-collection"
        assert validate_collection_name("col_2024-01") == "col_2024-01"

    def test_reject_empty(self):
        """Test rejection of empty collection name."""
        with pytest.raises(HTTPException) as exc_info:
            validate_collection_name("")
        assert exc_info.value.status_code == 400
        assert "cannot be empty" in exc_info.value.detail

    def test_reject_path_traversal(self):
        """Test rejection of path traversal attempts."""
        with pytest.raises(HTTPException) as exc_info:
            validate_collection_name("../admin")
        assert exc_info.value.status_code == 400

        with pytest.raises(HTTPException):
            validate_collection_name("../../secret")

        with pytest.raises(HTTPException):
            validate_collection_name("../")

    def test_reject_dot_patterns(self):
        """Test rejection of dot and double-dot."""
        with pytest.raises(HTTPException) as exc_info:
            validate_collection_name(".")
        assert exc_info.value.status_code == 400

        with pytest.raises(HTTPException):
            validate_collection_name("..")

    def test_reject_special_characters(self):
        """Test rejection of special characters."""
        invalid_names = [
            "col/name",  # slash
            "col\\name",  # backslash
            "col name",  # space
            "col@name",  # at sign
            "col#name",  # hash
            "col$name",  # dollar
            "col%name",  # percent
            "col&name",  # ampersand
            "col*name",  # asterisk
            "col(name)",  # parentheses
            "col.name",  # dot (not allowed in collections)
        ]
        for name in invalid_names:
            with pytest.raises(HTTPException):
                validate_collection_name(name)

    def test_reject_too_long(self):
        """Test rejection of names exceeding max length."""
        long_name = "a" * 65
        with pytest.raises(HTTPException):
            validate_collection_name(long_name)

    def test_max_length_allowed(self):
        """Test that 64 characters is allowed."""
        max_length_name = "a" * 64
        assert validate_collection_name(max_length_name) == max_length_name


class TestFilenameValidation:
    """Tests for filename validation."""

    def test_valid_filenames(self):
        """Test valid filenames."""
        assert validate_filename("test.txt") == "test.txt"
        assert validate_filename("my-file_v2.pdf") == "my-file_v2.pdf"
        assert validate_filename("document.tar.gz") == "document.tar.gz"

    def test_reject_empty(self):
        """Test rejection of empty filename."""
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("")
        assert exc_info.value.status_code == 400

    def test_reject_path_traversal(self):
        """Test rejection of path traversal in filenames."""
        with pytest.raises(HTTPException):
            validate_filename("../secret.txt")

        with pytest.raises(HTTPException):
            validate_filename("dir/file.txt")

        with pytest.raises(HTTPException):
            validate_filename("dir\\file.txt")

    def test_reject_dot_patterns(self):
        """Test rejection of . and .. as filenames."""
        with pytest.raises(HTTPException):
            validate_filename(".")

        with pytest.raises(HTTPException):
            validate_filename("..")

    def test_max_length(self):
        """Test filename length limits."""
        long_name = "a" * 256
        with pytest.raises(HTTPException):
            validate_filename(long_name)

        max_name = "a" * 255
        assert validate_filename(max_name) == max_name
