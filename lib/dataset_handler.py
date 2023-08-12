import os
import logging

class DatasetHandler(logging.Handler):

    _self = None
    def __new__(cls, filename, foldername):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self, filename: str, foldername: str):
        super().__init__()
        self.filename = os.path.join(foldername, filename)

    def emit(self, record):
        try:
            log_message = self.format(record)
            with open(self.filename, "a") as file:
                file.write(log_message + "\n")
        except (FileNotFoundError, FileExistsError) as exception:
            raise Exception() from exception
