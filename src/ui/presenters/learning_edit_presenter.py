from typing import Optional

from core import AppLogger, Algorithm, config
from models.model.model_metadata import ModelMetadata
from services import model_service
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class LearningEditPresenter(BasePresenter):
    def __init__(self, view):
        super().__init__(view)
        self.selected_model: Optional[ModelMetadata] = None
        self._initialize_data()

    def _initialize_data(self) -> None:
        try:
            model_service.refresh()
            logger.info("LearningEditPresenter initialized")
        except Exception as e:
            logger.exception("Error initializing LearningEditPresenter")

    def start(self) -> None:
        try:
            logger.info("LearningEditPresenter started")
        except Exception as e:
            logger.exception("Error starting LearningEditPresenter")

    def stop(self) -> None:
        logger.info("LearningEditPresenter stopped")

    def refresh(self) -> None:
        try:
            model_service.refresh()
            self.show_selected_model()
        except Exception as e:
            logger.exception("Error refreshing LearningEditPresenter")

    def set_model(self, model: ModelMetadata) -> None:
        try:
            self.selected_model = model
            self.show_selected_model()
            logger.info(f"Set model for editing: {model.name}")
        except Exception as e:
            logger.exception(f"Error setting model: {e}")

    def show_selected_model(self) -> None:
        try:
            if not self.selected_model:
                self.clear_model_data()
                return

            model = self.selected_model

            self.view.ids.model_name.text = model.name
            self.view.ids.created_date.text = model.created_format
            self.view.ids.author.text = model.author or "Unknown"
            self.view.ids.description.text = model.comment or ""

            if model.algorithm == Algorithm.KNN:
                self.view.ids.threshold_box.height = 30
                self.view.ids.threshold_box.opacity = 1
                self.view.ids.threshold.text = f"{model.threshold:.4f}"
                self.view.ids.threshold.disabled = True
                self.view.ids.manual_checkbox.active = False
            else:
                self.view.ids.threshold_box.height = 0
                self.view.ids.threshold_box.opacity = 0

            logger.info(f"Displayed model for editing: {model.name}")

        except Exception as e:
            logger.exception("Error showing selected model")
            self.clear_model_data()

    def clear_model_data(self) -> None:
        try:
            self.view.ids.model_name.text = ''
            self.view.ids.created_date.text = ''
            self.view.ids.author.text = ''
            self.view.ids.description.text = ''
            self.view.ids.threshold.text = ''
            self.view.ids.threshold_box.height = 0
            self.view.ids.threshold_box.opacity = 0
        except Exception as e:
            logger.exception("Error clearing model data")

    def enable_threshold_input(self, enabled: bool) -> None:
        try:
            if enabled:
                self.view.ids.threshold.disabled = False
                if self.selected_model:
                    self.view.ids.threshold.text = f"{self.selected_model.threshold:.4f}"
            else:
                self.view.ids.threshold.disabled = True
                if self.selected_model:
                    self.view.ids.threshold.text = f"{self.selected_model.threshold:.4f}"
        except Exception as e:
            logger.exception("Error enabling threshold input")

    def delete_description(self) -> None:
        try:
            self.view.ids.description.text = ""
            logger.info("Description cleared")
        except Exception as e:
            logger.exception("Error deleting description")

    def save_changes(self) -> bool:
        try:
            if not self.selected_model:
                self.show_error("Error", "No model selected")
                return False

            original_name = self.selected_model.name
            new_name = self.view.ids.model_name.text.strip()
            description = self.view.ids.description.text.strip()

            if not new_name:
                self.show_error("Error", "Model name cannot be empty")
                return False

            if new_name != original_name:
                existing = model_service.get_model(new_name)
                if existing:
                    self.show_error("Error", f"Model '{new_name}' already exists")
                    return False

            self.selected_model.comment = description

            if (self.selected_model.algorithm == Algorithm.KNN and
                    self.view.ids.manual_checkbox.active):
                try:
                    threshold = float(self.view.ids.threshold.text)
                    if not (0 <= threshold <= 1):
                        self.show_error("Error", "Threshold must be between 0 and 1")
                        return False
                    self.selected_model.threshold = threshold
                except ValueError:
                    self.show_error("Error", "Invalid threshold value")
                    return False

            if new_name != original_name:
                try:
                    model_service.registry.update(original_name, new_name)

                    from core import config
                    old_path = config.paths.MODEL_DATA_DIR / original_name
                    new_path = config.paths.MODEL_DATA_DIR / new_name

                    if old_path.exists() and not new_path.exists():
                        old_path.rename(new_path)
                        self.selected_model.name = new_name
                        logger.info(f"Renamed model: {original_name} -> {new_name}")

                except Exception as e:
                    logger.exception(f"Error renaming model: {e}")
                    self.show_error("Error", f"Failed to rename model: {str(e)}")
                    return False

            self.selected_model.save()

            self.show_info("Success", "Model changes saved")
            logger.info(f"Saved changes for model: {new_name}")
            return True

        except Exception as e:
            logger.exception(f"Error saving changes: {e}")
            self.show_error("Error", str(e))
            return False

    def delete_model(self, model_name: str) -> bool:
        try:
            success = model_service.delete_model(model_name)
            if success:
                self.selected_model = None
                self.clear_model_data()
                logger.info(f"Deleted model: {model_name}")
                return True
            else:
                self.show_error("Error", f"Failed to delete model '{model_name}'")
                return False

        except Exception as e:
            logger.exception(f"Error deleting model: {e}")
            self.show_error("Error", str(e))
            return False

    def get_default_threshold(self) -> str:
        return str(config.model.DEFAULT_THRESHOLD)

    def get_model_threshold(self) -> str:
        if self.selected_model:
            return f"{self.selected_model.threshold:.4f}"
        return self.get_default_threshold()
