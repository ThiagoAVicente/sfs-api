class JobRequest:

    def __init__(self, function: str, file_name: str, file_type:str|None=None):
        self.function = function
        self.file_name = file_name
        self.file_type = file_type
