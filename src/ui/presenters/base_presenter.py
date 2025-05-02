from abc import ABC, abstractmethod
from src.core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class BasePresenter(ABC):
    """Base class for all presenters."""

    def __init__(self, view):
        self.view = view

    @abstractmethod
    def start(self) -> None:
        """Start presenter operations."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop presenter operations."""
        pass

    def show_error(self, message: str) -> None:
        """Show error message."""
        logger.error(message)
        if self.view:
            self.view.show_error(message)

    def show_info(self, message: str) -> None:
        """Show info message."""
        logger.info(message)
        if self.view:
            self.view.show_info(message)
