from .tools import *
from .generate_gmsh import *
from .generate_mesh_occ import *
from .generate_pythonocc import *
from .generate_statistics import *
from .dataset_handler import DatasetHandler

import logging

class Logger:

    LOG_LEVEL = {"debug": logging.DEBUG,
                "info": logging.INFO, 
                "warn": logging.WARN, 
                "error": logging.ERROR}
    
    _instanced = False
    def __new__(cls):
        if cls._instanced is False:
            cls._instanced = super().__new__(cls)
            cls._instanced.value = True
        return cls._instanced

    def __init__(self, cls, filename: str = "", foldername: str = "", level: str = "error", stdout: bool = False):
        PROJECT_ROOT = get_project_root()
        if not len(foldername):
            foldername = os.path.join(PROJECT_ROOT, "/logs/")
            os.makedirs(foldername, exists=True)
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

        Logger._instanced = True

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
