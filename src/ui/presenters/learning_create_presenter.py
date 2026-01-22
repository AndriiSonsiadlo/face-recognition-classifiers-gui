import threading
import time
from typing import Optional, List

from kivy.clock import mainthread

from core import AppLogger, Algorithm, config
from models.model.model_metadata import ModelMetadata
from models.model.model_trainer import ModelTrainer
from services import model_service, person_service
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class LearningCreatePresenter(BasePresenter):
    def __init__(self, view):
        super().__init__(view)
        self.selected_algorithm: Algorithm = Algorithm.KNN
        self.selected_weight: str = "distance"
        self.selected_gamma: str = "scale"
        self.n_neighbors: Optional[int] = None
        self.use_auto_neighbors: bool = True
        self.is_training = False
        self.training_cancelled = False
        self.training_thread = None
        self._initialize_data()

    def _initialize_data(self) -> None:
        try:
            model_service.refresh()
            person_service.refresh()
            logger.info("LearningCreatePresenter initialized")
        except Exception as e:
            logger.exception("Error initializing LearningCreatePresenter")

    def start(self) -> None:
        try:
            self._update_view()
            logger.info("LearningCreatePresenter started")
        except Exception as e:
            logger.exception("Error starting LearningCreatePresenter")

    def stop(self) -> None:
        if self.is_training:
            self.cancel_training()
        logger.info("LearningCreatePresenter stopped")

    def refresh(self) -> None:
        try:
            model_service.refresh()
            person_service.refresh()
            self._update_view()
        except Exception as e:
            logger.exception("Error refreshing LearningCreatePresenter")

    def _update_view(self) -> None:
        try:
            self.selected_algorithm = Algorithm.KNN
            self._show_knn_controls()
            self._update_persons_list()
        except Exception as e:
            logger.exception("Error updating view")

    def get_algorithms(self) -> List[str]:
        return [Algorithm.KNN.value, Algorithm.SVM.value]

    def select_algorithm(self, algorithm_name: str) -> None:
        try:
            if algorithm_name == Algorithm.KNN.value:
                self.selected_algorithm = Algorithm.KNN
                self._show_knn_controls()
                logger.info("Selected KNN algorithm")
            elif algorithm_name == Algorithm.SVM.value:
                self.selected_algorithm = Algorithm.SVM
                self._show_svm_controls()
                logger.info("Selected SVM algorithm")
        except Exception as e:
            logger.exception(f"Error selecting algorithm: {e}")

    def _show_knn_controls(self) -> None:
        try:
            if hasattr(self.view.ids, 'neighbor_box'):
                self.view.ids.neighbor_box.height = 30
                self.view.ids.neighbor_box.opacity = 1

            if hasattr(self.view.ids, 'weights_box'):
                self.view.ids.weights_box.height = 30
                self.view.ids.weights_box.opacity = 1

            if hasattr(self.view.ids, 'gamma_box'):
                self.view.ids.gamma_box.height = 0
                self.view.ids.gamma_box.opacity = 0

            logger.info("KNN controls shown")
        except Exception as e:
            logger.exception("Error showing KNN controls")

    def _show_svm_controls(self) -> None:
        try:
            if hasattr(self.view.ids, 'gamma_box'):
                self.view.ids.gamma_box.height = 30
                self.view.ids.gamma_box.opacity = 1

            if hasattr(self.view.ids, 'neighbor_box'):
                self.view.ids.neighbor_box.height = 0
                self.view.ids.neighbor_box.opacity = 0

            if hasattr(self.view.ids, 'weights_box'):
                self.view.ids.weights_box.height = 0
                self.view.ids.weights_box.opacity = 0

            logger.info("SVM controls shown")
        except Exception as e:
            logger.exception("Error showing SVM controls")

    def get_weights(self) -> List[str]:
        return ["distance", "uniform"]

    def get_gammas(self) -> List[str]:
        return ["scale", "auto"]

    def on_weight_selected(self, weight: str) -> None:
        self.selected_weight = weight
        logger.info(f"Selected weight: {weight}")

    def on_gamma_selected(self, gamma: str) -> None:
        self.selected_gamma = gamma
        logger.info(f"Selected gamma: {gamma}")

    def on_neighbor_checkbox_active(self, is_active: bool) -> None:
        try:
            self.use_auto_neighbors = not is_active

            if hasattr(self.view.ids, 'create_neighbor_num'):
                self.view.ids.create_neighbor_num.disabled = not is_active

                if is_active:
                    self.view.ids.create_neighbor_num.text = str(self.n_neighbors or "")
                else:
                    self.view.ids.create_neighbor_num.text = ""
                    self.n_neighbors = None

            logger.info(f"Neighbor mode: {'manual' if is_active else 'auto'}")
        except Exception as e:
            logger.exception("Error handling neighbor checkbox")

    def set_n_neighbors(self, value: str) -> None:
        try:
            if not value or value.lower() == "auto" or value == "":
                self.n_neighbors = None
            else:
                try:
                    self.n_neighbors = int(value)
                    if self.n_neighbors < 1:
                        raise ValueError("n_neighbors must be >= 1")
                except ValueError as e:
                    logger.warning(f"Invalid n_neighbors value: {value}")
                    self.n_neighbors = None

            logger.info(f"Set n_neighbors: {self.n_neighbors}")
        except Exception as e:
            logger.exception("Error setting n_neighbors")

    def get_persons_with_photos(self) -> List[str]:
        try:
            persons = person_service.get_persons_with_photos(min_photos=1)
            return [p.name for p in persons]
        except Exception as e:
            logger.exception("Error getting persons with photos")
            return []

    def _update_persons_list(self) -> None:
        try:
            persons = self.get_persons_with_photos()
            if hasattr(self.view.ids, 'rv') and hasattr(self.view.ids, 'rv_box'):
                if persons:
                    self.view.ids.rv.data = [{'text': name} for name in persons]
                else:
                    self.view.ids.rv.data = [{'text': 'No persons with photos'}]
        except Exception as e:
            logger.exception("Error updating persons list")

    def search_persons(self, query: str) -> None:
        try:
            if not query:
                self._update_persons_list()
                return

            all_persons = self.get_persons_with_photos()
            query_lower = query.lower()
            matching = [p for p in all_persons if query_lower in p.lower()]

            if hasattr(self.view.ids, 'rv'):
                if matching:
                    self.view.ids.rv.data = [{'text': name} for name in matching]
                else:
                    self.view.ids.rv.data = [{'text': 'No matches'}]

        except Exception as e:
            logger.exception("Error searching persons")

    def begin_training(self) -> None:
        try:
            model_name = self.view.ids.create_model_name.text.strip()
            author = self.view.ids.create_author.text.strip()
            comment = self.view.ids.create_comment.text.strip()

            self.train_model(model_name, author, comment)

        except Exception as e:
            logger.exception("Error in begin_training")
            self.show_error("Error", str(e))

    def train_model(
            self,
            model_name: str,
            author: str,
            comment: str
    ) -> None:
        try:
            if not model_name or not model_name.strip():
                self.show_error("Error", "Model name is required")
                return

            if model_service.get_model(model_name):
                i = 1
                base_name = model_name
                while model_service.get_model(f"{base_name} ({i})"):
                    i += 1
                model_name = f"{base_name} ({i})"

            persons = self.get_persons_with_photos()
            if not persons:
                self.show_error("Error", "No persons with photos available for training")
                return

            self.training_cancelled = False

            self._show_training_progress()

            self.is_training = True
            self.training_thread = threading.Thread(
                target=self._train_model_thread,
                args=(model_name, author, comment),
                daemon=False
            )
            self.training_thread.start()

            logger.info(f"Started training model: {model_name}")

        except Exception as e:
            logger.exception(f"Error starting model training: {e}")
            self.show_error("Error", str(e))
            self._hide_training_progress()

    def cancel_training(self) -> None:
        try:
            if self.is_training:
                logger.info("Training cancellation requested")
                self.training_cancelled = True
                self._update_training_status("Cancelled")
                self._update_training_info("Cleaning up resources...")
        except Exception as e:
            logger.exception(f"Error cancelling training: {e}")

    def _show_training_progress(self) -> None:
        try:
            if hasattr(self.view, 'manager'):
                learning_mode = self.view.manager.get_screen("learning")
                if hasattr(learning_mode, 'show_training_progress'):
                    learning_mode.show_training_progress(
                        on_cancel=self.cancel_training
                    )
                    logger.info("Training progress popup shown")
        except Exception as e:
            logger.debug(f"Could not show progress popup: {e}")

    def _hide_training_progress(self) -> None:
        try:
            if hasattr(self.view, 'manager'):
                learning_mode = self.view.manager.get_screen("learning")
                if hasattr(learning_mode, 'hide_training_progress'):
                    learning_mode.hide_training_progress()
                    logger.info("Training progress popup hidden")
        except Exception as e:
            logger.debug(f"Could not hide progress popup: {e}")

    def _train_model_thread(self, model_name: str, author: str, comment: str) -> None:
        try:
            start_time = time.time()

            if self.training_cancelled:
                self._on_training_cancelled()
                return

            model = ModelMetadata(
                name=model_name,
                author=author or "Unknown",
                comment=comment or "",
                algorithm=self.selected_algorithm,
                learning_time=0,
                accuracy=0.0,
                threshold=config.model.DEFAULT_THRESHOLD,
                n_neighbors=self.n_neighbors if self.selected_algorithm == Algorithm.KNN else None,
                weight=self.selected_weight if self.selected_algorithm == Algorithm.KNN else None,
                gamma=self.selected_gamma if self.selected_algorithm == Algorithm.SVM else None,
            )

            if not model_service.registry.add(model):
                self._on_training_error("Failed to create model in registry")
                return

            if self.training_cancelled:
                model_service.delete_model(model_name)
                self._on_training_cancelled()
                return

            trainer = ModelTrainer(model)
            success = trainer.train()

            if self.training_cancelled:
                model_service.delete_model(model_name)
                self._on_training_cancelled()
                return

            learning_time = time.time() - start_time

            if success:
                model_service.refresh()
                trained_model = model_service.get_model(model_name)

                if trained_model:
                    if trained_model.json_path.exists():
                        logger.info(f"Model metadata JSON verified at: {trained_model.json_path}")
                        self._on_training_complete(
                            model_name,
                            learning_time,
                            trained_model.threshold,
                            trained_model.accuracy
                        )
                    else:
                        logger.error(f"Model metadata JSON not found at: {trained_model.json_path}")
                        self._on_training_error("Model metadata file was not created")
                else:
                    self._on_training_error("Model not found after training")
            else:
                model_service.delete_model(model_name)
                self._on_training_error("Model training failed")

        except Exception as e:
            logger.exception(f"Error in training thread: {e}")
            self._on_training_error(f"Training error: {str(e)}")
            try:
                model_service.delete_model(model_name)
            except:
                pass
        finally:
            self.is_training = False
            self.training_cancelled = False
            self._hide_training_progress()

    @mainthread
    def _on_training_complete(
            self,
            model_name: str,
            learning_time: float,
            threshold: float,
            accuracy: float
    ) -> None:
        try:
            self.view.manager.current = "learning"

            learning_mode = self.view.manager.get_screen("learning")
            if hasattr(learning_mode.presenter, 'refresh'):
                learning_mode.presenter.refresh()

            self.show_info(
                f"Model '{model_name}' trained successfully!\n\n"
                f"Time: {learning_time:.2f}s\n"
                f"Accuracy: {accuracy:.2%}\n"
                f"Threshold: {threshold:.2f}"
            )
            logger.info(f"Training completed successfully for: {model_name}")
        except Exception as e:
            logger.exception("Error in _on_training_complete")

    @mainthread
    def _on_training_error(self, error_message: str) -> None:
        try:
            self.show_error("Training Failed", error_message)
            logger.error(f"Training failed: {error_message}")
        except Exception as e:
            logger.exception("Error in _on_training_error")

    @mainthread
    def _on_training_cancelled(self) -> None:
        try:
            self.show_info("Cancelled", "Model training was cancelled")
            logger.info("Training was cancelled by user")
        except Exception as e:
            logger.exception("Error in _on_training_cancelled")

    def clear_inputs(self) -> None:
        try:
            self.view.ids.create_model_name.text = ''
            self.view.ids.create_author.text = ''
            self.view.ids.create_comment.text = ''
            self.view.ids.create_neighbor_num.text = ''

            self.selected_algorithm = Algorithm.KNN
            if hasattr(self.view.ids, 'spinner_algorithm'):
                self.view.ids.spinner_algorithm.text = Algorithm.KNN.value

            if hasattr(self.view.ids, 'neighbor_checkbox'):
                self.view.ids.neighbor_checkbox.active = False

            self.use_auto_neighbors = True
            self.n_neighbors = None

            self._show_knn_controls()

            if hasattr(self.view.ids, 'begin_learning_button'):
                self.view.ids.begin_learning_button.text = "Train model"
                self.view.ids.begin_learning_button.disabled = False
                self.view.ids.begin_learning_button.opacity = 1.0

            if hasattr(self.view.ids, 'learning_results'):
                self.view.ids.learning_results.opacity = 0

            self._update_persons_list()
            logger.info("Form inputs cleared")
        except Exception as e:
            logger.exception("Error clearing inputs")
