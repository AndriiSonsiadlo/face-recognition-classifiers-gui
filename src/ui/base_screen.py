from kivy.uix.screenmanager import Screen
from kivy.clock import mainthread
from abc import ABC, abstractmethod

from src.utils.logger import AppLogger


class BaseScreen(Screen):
    """Base class for all screens"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = AppLogger().get_logger()

    def refresh(self):
        """Called when screen is entered"""
        pass

    def show_error_popup(self, title: str, message: str = "") -> None:
        """Show error popup"""
        from classes.Popup.my_popup_warn import MyPopupWarn
        popup = MyPopupWarn(text=f"{title}\n{message}")
        popup.open()

    def show_info_popup(self, title: str) -> None:
        """Show info popup"""
        from classes.Popup.my_popup_info import MyPopupInfo
        popup = MyPopupInfo(text=title)
        popup.open()