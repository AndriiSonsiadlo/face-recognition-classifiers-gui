from kivy.uix.screenmanager import Screen

from core.logger import AppLogger


class BaseScreen(Screen):
    """Base class for all screens"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = AppLogger().get_logger()

    def refresh(self):
        """Called when screen is entered"""
        pass

    def show_error(self, title: str, message: str = "") -> None:
        """Show error popup"""
        from classes.Popup.my_popup_warn import MyPopupWarn
        popup = MyPopupWarn(text=f"{title}\n{message}")
        popup.open()

    def show_info(self, title: str) -> None:
        """Show info popup"""
        from classes.Popup.my_popup_info import MyPopupInfo
        popup = MyPopupInfo(text=title)
        popup.open()