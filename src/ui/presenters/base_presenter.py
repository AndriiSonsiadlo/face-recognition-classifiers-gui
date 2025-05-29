from abc import ABC, abstractmethod
from core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class BasePresenter(ABC):
    def __init__(self, view):
        self.view = view

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    def show_error(self, title:str, message: str="") -> None:
        logger.error(message)
        if self.view:
            self.view.show_error(title, message)

    def show_info(self, title:str, message: str="") -> None:
        logger.info(message)
        if self.view:
            self.view.show_info(title, message)
