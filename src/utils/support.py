import filetype

NS: str = "Not supported"


class FileTypeResponse:
    def __init__(self, val: bool, explanation: str, type: str | None = None):
        self.val = val
        self.explanation = explanation
        self.type = type


class FileType:
    _allowed_non_text: frozenset[str] = frozenset(["application/pdf"])

    @classmethod
    def is_supported(cls, file_content: bytes) -> FileTypeResponse:
        """
        Checks if the file content is supported by the system.
        Args:
            file_content (bytes): The content of the file to be checked.
        Returns:
            bool: True if the file content is supported, False otherwise.
        """

        kind = filetype.guess(file_content)
        if kind and kind.mime in cls._allowed_non_text:
            return FileTypeResponse(True, "", kind.extension)

        try:
            decoded = file_content.decode("utf-8")
        except UnicodeDecodeError:
            return FileTypeResponse(False, NS)

        if not decoded.strip():
            return FileTypeResponse(False, "empty file")

        if not decoded or not any(c.isprintable() and not c.isspace() for c in decoded):
            return FileTypeResponse(False, NS)

        return FileTypeResponse(True, "", "text")
