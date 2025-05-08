from kivy.uix.screenmanager import Screen

from core.logger import AppLogger


class BaseScreen(Screen):
    """Base class for all screens"""

    def __init__(self, logger_name=None, **kwargs):
        super().__init__(**kwargs)
        self.logger = AppLogger().get_logger(logger_name or "BaseScreen")

    def refresh(self) -> None:
        """Called when screen is entered - update UI."""
        try:
            if self.presenter:
                self.presenter.refresh()
            self.logger.info("Screen refreshed")
        except Exception as e:
            self.logger.exception("Error refreshing screen")
            self.show_error("Refresh Error", str(e))

    def show_error(self, title: str, message: str = "") -> None:
        """Show error popup"""
        from ui.popups.warn import WarnPopup
        popup = WarnPopup(title=f"{title}\n\n{message}")
        popup.open()

    def show_info(self, title: str, message: str = "") -> None:
        """Show info popup"""
        from ui.popups.info import InfoPopup
        popup = InfoPopup(title=f"{title}\n\n{message}")
        popup.open()

    def popup_photo(self, path: str) -> None:
        """Show photo in popup"""
        try:
            from ui.popups.plot import PlotPopup
            popup = PlotPopup(path)
            popup.open()
        except Exception:
            pass