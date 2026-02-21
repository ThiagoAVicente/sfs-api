from dataclasses import dataclass


@dataclass
class JobRequest:
    function: str
    file_path: str
    collection: str
    file_type: str | None = None
