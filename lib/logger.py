import os
import time
import logging
from .tools import get_project_root

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
        
class Logger():

    LOG_LEVEL = {"debug": logging.DEBUG,
                "info": logging.INFO, 
                "warn": logging.WARN, 
                "error": logging.ERROR}

    def __init__(self, filename: str = "", foldername: str = "", level: str = "error", stdout: bool = False):
        PROJECT_ROOT = get_project_root()
        if not len(foldername):
            foldername = os.path.join(PROJECT_ROOT, "/logs/")
            os.makedirs(foldername, exists=True)
        if not len(filename):
            filename = f"log_{time.time()}.txt"

        self.logger = logging.getLogger()
        self.logger.setLevel(Logger.LOG_LEVEL[level.lower()])

        formatter = logging.Formatter("'%(asctime)s - %(levelname)s - %(message)s")
        handler = DatasetHandler(filename, foldername)
        handler.setFormatter(formatter)

        if stdout:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)
        self.logger.addHandler(handler)

    def log(self, message, level):
        level = level.lower()
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warn":
            self.logger.warn(message)
        elif level == "error":
            self.logger.error(message)
        else:
            self.logger.warning("Log Level not supported.")
