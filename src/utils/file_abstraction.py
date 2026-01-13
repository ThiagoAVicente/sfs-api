from pypdf import PdfReader
from io import BytesIO

class FileAbstraction:
    @staticmethod
    def get_text(file_data: bytes, file_type: str) -> str:
        """
        Extracts text from a file based on its type.
        Args:
            file_data (bytes): The file data.
            file_type (str): The type of the file.
        Returns:
            str: The extracted text from the file.
        """
        if file_type == 'text':
            return file_data.decode('utf-8', errors="replace")

        elif file_type == 'pdf':
            return FileAbstraction._pdf_to_text(file_data)

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _pdf_to_text(file_data: bytes) -> str:
        """
        Converts a PDF file to text.
        Args:
            file_data (bytes): The PDF file data.
        Returns:
            str: The extracted text from the PDF.
        """
        reader = PdfReader(BytesIO(file_data))
        text_parts: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text_parts.append(page_text)

        return "\n".join(text_parts)
