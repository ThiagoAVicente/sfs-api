class JobRequest:

    def __init__(self, function: str, file_path: str, file_type:str|None=None):
        self.function = function
        self.file_path = file_path
        self.file_type = file_type
