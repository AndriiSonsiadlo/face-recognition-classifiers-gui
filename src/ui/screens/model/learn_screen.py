from typing import Optional

from kivy.clock import mainthread

from core import AppLogger
from ui.base_screen import BaseScreen
from ui.popups.training_progress import TrainingProgressPopup
from ui.presenters.learning_mode_presenter import LearningModePresenter

logger = AppLogger().get_logger(__name__)

class LearningMode(BaseScreen):
    screen = None

    def __init__(self, **kwargs):
        super().__init__(__name__, **kwargs)
        LearningMode.screen = self

        self.presenter: Optional['LearningModePresenter'] = None
        self.training_popup: Optional[TrainingProgressPopup] = None
        self._initialize()

    def _initialize(self) -> None:
        try:
            self.presenter = LearningModePresenter(self)
            self.presenter.start()
            logger.info("LearningMode initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing LearningMode: {e}")
            self.show_error("Initialization Error", str(e))

    def on_pre_enter(self) -> None:
        try:
            self.refresh()
        except Exception as e:
            self.logger.exception("Error on_pre_enter")

    def refresh(self) -> None:
        try:
            if self.presenter:
                self.presenter.refresh()
            logger.info("LearningMode refreshed")
        except Exception as e:
            self.logger.exception("Error refreshing LearningMode")

    def on_model_selected(self, model_name: str) -> None:
        try:
            if self.presenter:
                self.presenter.select_model(model_name)
        except Exception as e:
            self.logger.exception("Error selecting model")

    def search_persons(self, query: str) -> None:
        try:
            if self.presenter:
                self.presenter.search_persons(query)
        except Exception as e:
            self.logger.exception("Error searching persons")

    def create_new_model(self) -> None:
        try:
            self.manager.transition.direction = "left"
            self.manager.current = "learning_create"
        except Exception as e:
            self.logger.exception("Error navigating to create model")

    def edit_model(self) -> None:
        try:
            if not self.presenter or not self.presenter.selected_model:
                self.show_error("Error", "No model selected")
                return

            edit_screen = self.manager.get_screen("learning_edit")
            edit_screen.model = self.presenter.selected_model

            self.manager.transition.direction = "left"
            self.manager.current = "learning_edit"

            logger.info(f"Editing model: {self.presenter.selected_model.name}")

        except Exception as e:
            self.logger.exception("Error editing model")
            self.show_error("Error", str(e))

    def delete_model(self) -> None:
        try:
            if not self.presenter or not self.presenter.selected_model:
                self.show_error("Error", "No model selected")
                return

            from ui.popups.delete import DeleteModelPopup
            popup = DeleteModelPopup(self.presenter.selected_model.name)
            popup.bind(on_dismiss=self._on_model_deleted)
            popup.open()

        except Exception as e:
            self.logger.exception("Error deleting model")
            self.show_error("Error", str(e))

    @mainthread
    def _on_model_deleted(self, instance) -> None:
        try:
            if self.presenter:
                self.presenter.selected_model = None

            self.refresh()

            if self.presenter:
                self.presenter.clear_model_data()

            if hasattr(self.ids, 'model_name'):
                model_names = self.presenter.get_model_names()
                self.ids.model_name.values = model_names

                if model_names:
                    self.ids.model_name.text = model_names[0]
                    self.presenter.select_model(model_names[0])
                else:
                    self.ids.model_name.text = "No models"

            logger.info("Model deleted and UI refreshed")

        except Exception as e:
            self.logger.exception("Error on model deleted")

    def show_training_progress(self, on_cancel=None) -> None:
        try:
            self.training_popup = TrainingProgressPopup(on_cancel_callback=on_cancel)
            self.training_popup.open()
            logger.info("Training progress popup opened")
        except Exception as e:
            self.logger.exception("Error showing training progress")

    @mainthread
    def hide_training_progress(self) -> None:
        try:
            if self.training_popup:
                self.training_popup.dismiss()
                self.training_popup = None
            logger.info("Training progress popup closed")
        except Exception as e:
            self.logger.exception("Error hiding training progress")

    def on_leave(self) -> None:
        try:
            if self.training_popup:
                self.training_popup.dismiss()
                self.training_popup = None

            if self.presenter:
                self.presenter.stop()
            logger.info("LearningMode screen left")
        except Exception as e:
            self.logger.exception("Error on_leave")
