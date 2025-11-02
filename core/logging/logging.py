import logging
import os


class Logger:
    _logger = None

    @classmethod
    def setup_logging(cls):
        # Get log level from environment variable, default to INFO
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),  # Convert string to logging level
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),  # Log to console
                logging.FileHandler("app.log", mode="a")  # Log to file
            ]
        )
        cls._logger = logging.getLogger("ApplicationLogger")

    @classmethod
    def debug(cls, message):
        cls._logger.debug(message)

    @classmethod
    def info(cls, message):
        cls._logger.info(message)

    @classmethod
    def warning(cls, message):
        cls._logger.warning(message)

    @classmethod
    def error(cls, message):
        cls._logger.error(message)

    @classmethod
    def critical(cls, message):
        cls._logger.critical(message)


