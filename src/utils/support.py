import filetype

NS:str = "Not supported"

class FileType:
    _allowed_non_text:frozenset[str] = frozenset(['application/pdf'])

    @classmethod
    def is_supported(cls, file_content:bytes) -> tuple[bool,str]:
        """
        Checks if the file content is supported by the system.
        Args:
            file_content (bytes): The content of the file to be checked.
        Returns:
            bool: True if the file content is supported, False otherwise.
        """

        kind = filetype.guess(file_content)
        if kind and kind.mime in cls._allowed_non_text:
            return True,""

        try:
            decoded = file_content.decode('utf-8')
        except UnicodeDecodeError:
            return False, NS

        if not decoded.strip():
            return False, "Empty file"

        if not decoded or not any(c.isprintable() and not c.isspace() for c in decoded):
            return False, NS

        return True, ""
