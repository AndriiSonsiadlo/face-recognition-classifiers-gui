from typing import Optional

from core import AppLogger
from ui.base_screen import BaseScreen
from ui.presenters.learning_edit_presenter import LearningEditPresenter

logger = AppLogger().get_logger(__name__)


class LearningEdit(BaseScreen):
    model = None

    def __init__(self, **kwargs):
        super().__init__(__name__, **kwargs)
        self.presenter: Optional['LearningEditPresenter'] = None
        self._initialize()

    def _initialize(self) -> None:
        try:
            self.presenter = LearningEditPresenter(self)
            self.presenter.start()
            logger.info("LearningEdit initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing LearningEdit: {e}")
            self.show_error("Initialization Error", str(e))

    def on_pre_enter(self) -> None:
        try:
            if self.model and self.presenter:
                self.presenter.set_model(self.model)
            self.clear_inputs()
        except Exception as e:
            self.logger.exception("Error on_pre_enter")

    def clear_inputs(self) -> None:
        try:
            if self.ids.manual_checkbox:
                self.ids.manual_checkbox.active = False
            self.presenter.enable_threshold_input(False)
        except Exception as e:
            self.logger.exception("Error clearing inputs")

    def enable_threshold_input(self, enabled: bool) -> None:
        try:
            if self.presenter:
                self.presenter.enable_threshold_input(enabled)
        except Exception as e:
            self.logger.exception("Error enabling threshold input")

    def delete_description(self) -> None:
        try:
            if self.presenter:
                self.presenter.delete_description()
        except Exception as e:
            self.logger.exception("Error deleting description")

    def save_changes(self) -> None:
        try:
            if not self.presenter:
                self.show_error("Error", "Presenter not initialized")
                return

            success = self.presenter.save_changes()
            if success:
                self._navigate_back()

        except Exception as e:
            self.logger.exception("Error saving changes")
            self.show_error("Error", str(e))

    def delete_model(self) -> None:
        try:
            if not self.model:
                self.show_error("Error", "No model selected")
                return

            from ui.popups.delete import DeleteModelPopup
            popup = DeleteModelPopup(self.model.name)
            popup.bind(on_dismiss=self._on_model_deleted)
            popup.open()

        except Exception as e:
            self.logger.exception("Error deleting model")
            self.show_error("Error", str(e))

    def _on_model_deleted(self, instance) -> None:
        try:
            self._navigate_back()
        except Exception as e:
            self.logger.exception("Error on model deleted")

    def _navigate_back(self) -> None:
        try:
            self.manager.transition.direction = "right"
            self.manager.current = "learning"
        except Exception as e:
            self.logger.exception("Error navigating back")

    def on_leave(self) -> None:
        try:
            if self.presenter:
                self.presenter.stop()
            logger.info("LearningEdit screen left")
        except Exception as e:
            self.logger.exception("Error on_leave")
