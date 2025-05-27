from kivy.uix.screenmanager import Screen

from core.logger import AppLogger


class BaseScreen(Screen):
    def __init__(self, logger_name=None, **kwargs):
        super().__init__(**kwargs)
        self.logger = AppLogger().get_logger(logger_name or "BaseScreen")

    def refresh(self) -> None:
        try:
            if self.presenter:
                self.presenter.refresh()
            self.logger.info("Screen refreshed")
        except Exception as e:
            self.logger.exception("Error refreshing screen")
            self.show_error("Refresh Error", str(e))

    def show_error(self, title: str, message: str = "") -> None:
        from ui.popups.warn import WarnPopup
        WarnPopup(title=f"{title}\n\n{message}").open()

    def show_info(self, title: str, message: str = "") -> None:
        from ui.popups.info import InfoPopup
        if message:
            popup = InfoPopup(title=f"{title}\n\n{message}")
        else:
            popup = InfoPopup(title=title)
        popup.open()

    def popup_photo(self, path: str) -> None:
        try:
            from ui.popups.plot import PlotPopup
            PlotPopup(path).open()
        except Exception:
            pass