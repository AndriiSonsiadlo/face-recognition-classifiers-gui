import logging
from pathlib import Path
from datetime import datetime


class AppLogger:
    """Centralized logging with shared handlers but different named loggers."""

    _instance = None
    _handlers_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_handlers()
        return cls._instance

    def _initialize_handlers(self):
        """Initialize shared handlers only once."""

        if AppLogger._handlers_initialized:
            return

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

        # Shared formatter
        self.formatter = logging.Formatter(
            '[%(levelname)-7s] %(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s'
        )

        # File handler
        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)

        # Console handler
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.INFO)
        self.console_handler.setFormatter(self.formatter)

        AppLogger._handlers_initialized = True

    def get_logger(self, name: str = "AIApp") -> logging.Logger:
        """Return a named logger with shared handlers attached."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        logger.handlers.clear()

        logger.addHandler(self.file_handler)
        logger.addHandler(self.console_handler)

        return logger

