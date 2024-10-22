import os
import logging
import logging.config
import configparser


class Logger:
    _instance = None
    LOG_CONFIG_FILE = './configs/logger.ini'

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        if not os.path.isfile(self.LOG_CONFIG_FILE):
            raise FileNotFoundError(f"Logging configuration file not found: {self.LOG_CONFIG_FILE}")
        # Parse the configuration file to get the log file path, to create it if not exist
        config = configparser.ConfigParser()
        config.read(self.LOG_CONFIG_FILE)
        log_file_path = None
        if 'handler_fileHandler' in config:
            args = config['handler_fileHandler'].get('args')
            if args:
                args = args.strip("()")
                log_file_path = args.split(',')[0].strip().strip('\'"')
        if log_file_path:
            log_dir = os.path.dirname(log_file_path)
            os.makedirs(log_dir, exist_ok=True)
        logging.config.fileConfig(self.LOG_CONFIG_FILE)
        self.logger = logging.getLogger()
        self._initialized = True

    def get_logger(self):
        return self.logger
