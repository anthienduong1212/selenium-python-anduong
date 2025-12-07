import logging
import os
import sys
from typing import Optional


class Logger:
    _logger: Optional[logging.Logger] = None

    @classmethod
    def setup_logging(cls):
        """
        Configure the main logger for the application.
        Read the log level from the LOG_LEVEL environment variable (default is INFO).
        Configure logging to the console and the 'app.log' file.
        """
        if cls._logger is not None:
            return

        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)

        file_handler = logging.FileHandler("app.log", mode="a", encoding="utf-8")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.enconding = "utf-8"

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                console_handler,
                file_handler
            ]
        )
        cls._logger = logging.getLogger("SeleniumPythonLogger")
        cls._logger.info(f"Logger configured with level: {log_level_str}")

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Helper to ensure logger is initialized before use."""
        if cls._logger is None:
            cls.setup_logging()
        return cls._logger

    @classmethod
    def debug(cls, message):
        cls.get_logger().debug(message)

    @classmethod
    def info(cls, message):
        cls.get_logger().info(message)

    @classmethod
    def warning(cls, message):
        cls.get_logger().warning(message)

    @classmethod
    def error(cls, message):
        cls.get_logger().error(message)

    @classmethod
    def critical(cls, message):
        cls.get_logger().critical(message)


