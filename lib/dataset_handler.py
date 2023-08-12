import os
import logging

class DatasetHandler(logging.Handler):

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
