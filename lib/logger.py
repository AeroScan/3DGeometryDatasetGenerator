import os
import logging

from .tools import get_current_timestamp, get_project_root
from .dataset_handler import DatasetHandler

class Logger:

    LOG_LEVEL = {"debug": logging.DEBUG,
                 "info": logging.INFO,
                 "warn": logging.WARN,
                 "error": logging.ERROR}

    def __init__(self, filename: str = "", foldername: str = "", level: str = "error", stdout: bool = False):
        if not len(foldername):
            foldername = os.path.join(get_project_root(), "logs")
            os.makedirs(foldername, exist_ok=True)
        if not len(filename):
            filename = f"log_{get_current_timestamp()}.txt"

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
        """Shows the log based on log level.

        Arguments
        ---
        message: data to be shown in the log
        level: the log level. Possible levels are: debug, info, warn, error
        """
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
