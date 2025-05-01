import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import face_recognition
import numpy as np
from PIL import ImageDraw, Image

from src.core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class FaceEncoding:
    """Represents a face encoding with its label."""

    def __init__(self, encoding: np.ndarray, name: str):
        self.encoding = encoding
        self.name = name

    def to_tuple(self) -> Tuple[np.ndarray, str]:
        return (self.encoding, self.name)


class ClassifierBase(ABC):
    """Abstract base class for face classifiers."""

    MAX_WORKERS = 8
    TRAIN_SPLIT_THRESHOLD = 5
    UNKNOWN_LABEL = "Unknown"

    def __init__(self, model_name: str, model_path: Optional[Path] = None, verbose: bool = True):
        self.model_name = model_name
        self.model_path = model_path or Path("model.clf")
        self.verbose = verbose

        self.train_data: List[FaceEncoding] = []
        self.test_data: List[FaceEncoding] = []
        self.classifier = None
        self.accuracy = 0.0

        self.identified_name = ""
        self.counter_frame = 0

    @abstractmethod
    def train(self) -> bool:
        pass

    @abstractmethod
    def predict(self, encoding: np.ndarray) -> str:
        """Predict label for a single face encoding."""
        pass

    def load_model(self) -> bool:
        try:
            if not self.model_path.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                return False

            with open(self.model_path, 'rb') as f:
                self.classifier = pickle.load(f)
            logger.info(f"Model loaded successfully from {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model from {self.model_path}: {e}")
            return False

    def save_model(self) -> bool:
        """Save trained model to disk."""
        if self.classifier is None:
            logger.error("No classifier to save")
            return False

        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.classifier, f)
            logger.info(f"Model saved successfully to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Cannot save model: {e}")
            return False

    def predict_from_image(self, image_path: str) -> Tuple[np.ndarray, str]:
        if self.classifier is None:
            raise ValueError("Classifier not trained or loaded")

        try:
            image = self._load_and_resize_image(image_path)
            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                return image, self.UNKNOWN_LABEL

            face_encodings = face_recognition.face_encodings(
                image,
                known_face_locations=face_locations
            )

            predictions = [
                (self.predict(enc), loc) for enc, loc in zip(face_encodings, face_locations)
            ]

            return self._draw_predictions_on_image(image, predictions)

        except Exception as e:
            logger.exception(f"Error predicting from image {image_path}: {e}")
            raise

    def predict_webcam(self, frame: np.ndarray) -> Tuple[np.ndarray, int, str]:
        if self.classifier is None:
            raise ValueError("Classifier not trained or loaded")

        try:
            face_locations = face_recognition.face_locations(frame)

            if not face_locations:
                self.counter_frame = 0
                return frame, self.counter_frame, ""

            face_encodings = face_recognition.face_encodings(frame, face_locations)
            predictions = [
                (self.predict(enc), loc) for enc, loc in zip(face_encodings, face_locations)
            ]

            return self._draw_predictions_on_webcam(frame, predictions)

        except Exception as e:
            logger.exception(f"Error predicting from webcam frame: {e}")
            return frame, 0, ""

    @staticmethod
    def _load_and_resize_image(image_path: str, max_dimension: int = 400) -> np.ndarray:
        """Load and resize image to manageable size."""
        image = face_recognition.load_image_file(image_path)
        h, w = image.shape[:2]

        if w < h:
            new_w = max_dimension
            new_h = int(h * (max_dimension / w))
        else:
            new_h = max_dimension
            new_w = int(w * (max_dimension / h))

        return cv2.resize(image, (new_w, new_h))

    @staticmethod
    def _draw_predictions_on_image(image: np.ndarray, predictions: List) -> Tuple[np.ndarray, str]:
        """Draw prediction boxes and labels on image."""
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        last_name = ClassifierBase.UNKNOWN_LABEL

        for name, (top, right, bottom, left) in predictions:
            last_name = name
            draw.rectangle(((left, top), (right, bottom)), outline=(0, 255, 0), width=2)
            draw.text((left, top - 10), str(name), fill=(0, 255, 0))

        del draw
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR), last_name

    def _draw_predictions_on_webcam(self, frame: np.ndarray, predictions: List) -> Tuple[np.ndarray, int, str]:
        """Draw prediction boxes and labels on webcam frame."""
        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_frame)

        current_name = None

        for name, (top, right, bottom, left) in predictions:
            current_name = name
            draw.rectangle(((left, top), (right, bottom)), outline=(0, 255, 0), width=2)
            draw.text((left, top - 10), str(name), fill=(0, 255, 0))

        del draw
        frame = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)

        # Update frame counter for stable identification
        if len(predictions) == 1 and current_name:
            if self.identified_name == current_name:
                self.counter_frame += 1
            elif current_name != self.UNKNOWN_LABEL:
                self.identified_name = current_name
                self.counter_frame = 0
        else:
            self.counter_frame = 0

        return frame, self.counter_frame, self.identified_name
