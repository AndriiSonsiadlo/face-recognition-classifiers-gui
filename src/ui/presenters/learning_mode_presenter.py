from typing import Optional, List

from core import AppLogger, Algorithm, config
from models.model.model_metadata import ModelMetadata
from services import model_service, person_service
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class LearningModePresenter(BasePresenter):
    def __init__(self, view):
        super().__init__(view)
        self.selected_model: Optional[ModelMetadata] = None
        self._initialize_data()

    def _initialize_data(self) -> None:
        try:
            model_service.refresh()
            person_service.refresh()

            models = model_service.get_all_models()
            if models:
                self.selected_model = models[0]

            logger.info("LearningModePresenter initialized")
        except Exception as e:
            logger.exception("Error initializing LearningModePresenter")

    def start(self) -> None:
        try:
            self._update_view()
            logger.info("LearningModePresenter started")
        except Exception as e:
            logger.exception("Error starting LearningModePresenter")

    def stop(self) -> None:
        logger.info("LearningModePresenter stopped")

    def refresh(self) -> None:
        try:
            model_service.refresh()
            person_service.refresh()
            self._update_view()
            logger.info("LearningModePresenter refreshed")
        except Exception as e:
            logger.exception("Error refreshing LearningModePresenter")

    def _update_view(self) -> None:
        try:
            if hasattr(self.view.ids, 'model_name'):
                self.view.ids.model_name.values = self.get_model_names()
                if self.selected_model:
                    self.view.ids.model_name.text = self.selected_model.name
                if not self.selected_model and self.view.ids.model_name.values:
                    first_model = self.view.ids.model_name.values[0]
                    self.select_model(first_model)
                self.show_selected_model()
        except Exception as e:
            logger.exception("Error updating view")

    def get_model_names(self) -> List[str]:
        try:
            models = model_service.get_all_models()
            if not models:
                return []
            return [m.name for m in models]
        except Exception as e:
            logger.exception("Error getting model names")
            return []

    def get_selected_model(self) -> Optional[ModelMetadata]:
        return self.selected_model

    def select_model(self, model_name: str) -> bool:
        try:
            model = model_service.get_model(model_name)
            if model:
                self.selected_model = model
                self.show_selected_model()
                logger.info(f"Selected model: {model_name}")
                return True
            else:
                logger.warning(f"Model not found: {model_name}")
                return False

        except Exception as e:
            logger.exception(f"Error selecting model {model_name}")
            return False

    def show_selected_model(self) -> None:
        try:
            if not self.selected_model:
                self.clear_model_data()
                return

            model = self.selected_model

            self.view.ids.model_name.text = model.name
            self.view.ids.created_date.text = model.created_format
            self.view.ids.author.text = model.author or "Unknown"
            self.view.ids.comment.text = model.comment or "No description"
            self.view.ids.comment.opacity = 1 if model.comment else 0

            self.view.ids.algorithm_text.text = model.algorithm.value

            if model.algorithm == Algorithm.KNN:
                self._show_knn_params(model)
            elif model.algorithm == Algorithm.SVM:
                self._show_svm_params(model)

            self.view.ids.learning_time.text = f"{model.learning_time}s"
            self.view.ids.accuracy.text = f"{model.accuracy:.2%}"
            self.view.ids.num_trained.text = str(len(model.train_dataset_Y))
            self.view.ids.num_tested.text = str(len(model.test_dataset_Y))

            self.show_model_persons()

            self._enable_button(self.view.ids.edit_btn)
            self._enable_button(self.view.ids.delete_btn)

            logger.info(f"Displayed model: {model.name}")

        except Exception as e:
            logger.exception("Error showing selected model")
            self.clear_model_data()

    def _show_knn_params(self, model: ModelMetadata) -> None:
        try:
            self.view.ids.neighbor_box.height = 30
            self.view.ids.neighbor_box.opacity = 1
            self.view.ids.weight_box.height = 30
            self.view.ids.weight_box.opacity = 1
            self.view.ids.threshold_box.height = 30
            self.view.ids.threshold_box.opacity = 1

            self.view.ids.gamma_box.height = 0
            self.view.ids.gamma_box.opacity = 0

            self.view.ids.num_neighbors.text = str(model.n_neighbors or "auto")
            self.view.ids.weight.text = model.weight or "distance"
            self.view.ids.threshold.text = f"{model.threshold:.4f}"

        except Exception as e:
            logger.exception("Error showing KNN params")

    def _show_svm_params(self, model: ModelMetadata) -> None:
        try:
            self.view.ids.gamma_box.height = 30
            self.view.ids.gamma_box.opacity = 1

            self.view.ids.neighbor_box.height = 0
            self.view.ids.neighbor_box.opacity = 0
            self.view.ids.weight_box.height = 0
            self.view.ids.weight_box.opacity = 0
            self.view.ids.threshold_box.height = 0
            self.view.ids.threshold_box.opacity = 0

            self.view.ids.gamma.text = model.gamma or "scale"

        except Exception as e:
            logger.exception("Error showing SVM params")

    def show_model_persons(self) -> None:
        try:
            if not self.selected_model:
                self._set_empty_persons_list()
                return

            model = self.selected_model
            if len(model.train_dataset_Y):
                self.view.ids.train_dataset.opacity = 1
                self.view.ids.rv.data = [{'text': name} for name in model.train_dataset_Y]
            else:
                self._set_empty_persons_list()

            logger.info(f"Displayed {len(model.train_dataset_Y)} persons in model")

        except Exception as e:
            logger.exception("Error showing model persons")
            self._set_empty_persons_list()

    def _set_empty_persons_list(self) -> None:
        try:
            self.view.ids.rv.data = [{'text': config.ui.TEXTS["no_persons"]}]
        except Exception as e:
            logger.exception("Error setting empty persons list")

    def clear_model_data(self) -> None:
        try:
            self.view.ids.model_name.text = "N/A"
            self.view.ids.created_date.text = "N/A"
            self.view.ids.author.text = "N/A"
            self.view.ids.comment.text = "No description"
            self.view.ids.comment.opacity = 0
            self.view.ids.algorithm_text.text = "N/A"
            self.view.ids.learning_time.text = "N/A"
            self.view.ids.accuracy.text = "N/A"
            self.view.ids.num_trained.text = "N/A"
            self.view.ids.num_tested.text = "N/A"
            self.view.ids.num_neighbors.text = "N/A"
            self.view.ids.weight.text = "N/A"
            self.view.ids.threshold.text = "N/A"
            self.view.ids.gamma.text = "N/A"

            self.view.ids.neighbor_box.height = 0
            self.view.ids.neighbor_box.opacity = 0
            self.view.ids.weight_box.height = 0
            self.view.ids.weight_box.opacity = 0
            self.view.ids.threshold_box.height = 0
            self.view.ids.threshold_box.opacity = 0
            self.view.ids.gamma_box.height = 0
            self.view.ids.gamma_box.opacity = 0

            self._set_empty_persons_list()

            self._disable_button(self.view.ids.edit_btn)
            self._disable_button(self.view.ids.delete_btn)

        except Exception as e:
            logger.exception("Error clearing model data")

    def search_persons(self, query: str) -> None:
        try:
            if not self.selected_model:
                self._set_empty_persons_list()
                return

            if not query:
                self.show_model_persons()
                return

            query_lower = query.lower()
            matching = [
                name for name in self.selected_model.train_dataset_Y
                if query_lower in name.lower()
            ]

            if matching:
                self.view.ids.rv.data = [{'text': name} for name in matching]
            else:
                self.view.ids.rv.data = [{'text': 'No matches'}]

        except Exception as e:
            logger.exception("Error searching persons")

    def delete_model(self, model_name: str) -> bool:
        try:
            success = model_service.delete_model(model_name)
            if success:
                if self.selected_model and self.selected_model.name == model_name:
                    models = model_service.get_all_models()
                    self.selected_model = models[0] if models else None

                self.refresh()
                logger.info(f"Deleted model: {model_name}")
                return True
            else:
                logger.warning(f"Failed to delete model: {model_name}")
                return False

        except Exception as e:
            logger.exception(f"Error deleting model {model_name}: {e}")
            return False

    def _enable_button(self, button) -> None:
        try:
            button.disabled = False
            button.opacity = 1.0
        except Exception as e:
            logger.exception("Error enabling button")

    def _disable_button(self, button) -> None:
        try:
            button.disabled = True
            button.opacity = 0.5
        except Exception as e:
            logger.exception("Error disabling button")
