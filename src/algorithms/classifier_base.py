import math
import pickle
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import face_recognition
import numpy as np
from PIL import ImageDraw, Image
from face_recognition.face_recognition_cli import image_files_in_folder
from sklearn import metrics

from algorithms.face_encoding import FaceEncoding
from core import config
from utils.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class ClassifierBase(ABC):
    """Abstract base class for face classifiers."""

    MAX_WORKERS = 8
    TRAIN_SPLIT_THRESHOLD = 5  # Images with index > 5 go to test set
    UNKNOWN_LABEL = config.ui.TEXTS["unknown"]

    def __init__(self, model_name: str, model_path: Path, verbose: bool = True):
        self.model_name = model_name
        self.model_path = model_path
        self.verbose = verbose

        self.train_data: List[FaceEncoding] = []
        self.test_data: List[FaceEncoding] = []
        self.classifier = None
        self.accuracy = 0.0

        self.identified_name = ""
        self.counter_frame = 0

    @abstractmethod
    def train(self) -> Tuple[bool, str]:
        """Train the classifier. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def predict(self, encoding: np.ndarray) -> str:
        """Predict label for a single face encoding."""
        pass

    def load_model(self) -> bool:
        """Load pre-trained model from disk."""
        try:
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

    @staticmethod
    def _partition_list(items: List, num_parts: int) -> List[List]:
        """Partition a list into roughly equal parts."""
        part_size = math.ceil(len(items) / num_parts)
        return [items[part_size * i: part_size * (i + 1)] for i in range(num_parts)]

    def _load_images_from_persons(self, person_names: List[str]) -> int:
        """Load face encodings from person directories."""
        for name in person_names:
            person_photo_path = config.paths.get_dir_person_photo(name)
            if not person_photo_path.is_dir():
                continue

            is_trained = False
            is_tested = False

            image_paths = image_files_in_folder(str(person_photo_path))
            for index, img_path in enumerate(image_paths):
                encoding = self._extract_face_encoding(img_path)

                if encoding is None:
                    continue

                # Split into train/test based on index
                if index > self.TRAIN_SPLIT_THRESHOLD or index == 1:
                    self.test_data.append(FaceEncoding(encoding, name))
                    is_tested = True
                    logger.info(f"Added to test set: {name}")
                else:
                    self.train_data.append(FaceEncoding(encoding, name))
                    is_trained = True

            if not is_trained:
                logger.warning(f"Person {name} has no training data")
            if not is_tested:
                logger.warning(f"Person {name} has no test data")

        return len(self.train_data)

    def _extract_face_encoding(self, image_path: str) -> Optional[np.ndarray]:
        """Extract face encoding from image if exactly one face is found."""
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)

            if len(face_locations) < 1:
                logger.warning(f"Image {image_path} not suitable: 'Didn't find a face'")
                return None
            elif len(face_locations) > 1:
                logger.warning(f"Image {image_path} not suitable: 'Found more than one face'")
                return None

            encoding = face_recognition.face_encodings(
                image,
                known_face_locations=face_locations
            )[0]
            return encoding
        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")
            return None

    def _prepare_training_data(self) -> Tuple[List, List]:
        """Prepare training features and labels."""
        X_train = [enc.encoding for enc in self.train_data]
        y_train = [enc.name for enc in self.train_data]
        return X_train, y_train

    def _prepare_test_data(self) -> Tuple[List, List]:
        """Prepare test features and labels."""
        X_test = [enc.encoding for enc in self.test_data]
        y_test = [enc.name for enc in self.test_data]
        return X_test, y_test

    def _load_training_data(self) -> bool:
        """Load all training data using parallel processing."""
        # Discover all person directories
        train_dir = Path(folder_persons_data)
        persons = [
            p.name for p in train_dir.iterdir()
            if p.is_dir() and p.name != "temp" and (p / folder_person_photo).is_dir()
        ]

        if not persons:
            return False

        # Partition and load in parallel
        partitions = self._partition_list(persons, self.MAX_WORKERS)

        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = [executor.submit(self._load_images_from_persons, part) for part in partitions]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in parallel loading: {e}")

        return len(self.train_data) > 0

    def evaluate(self) -> None:
        """Evaluate classifier on test set."""
        if not self.test_data or self.classifier is None:
            logger.warning("No test data or classifier for evaluation")
            return

        X_test, y_test = self._prepare_test_data()
        y_pred = self.classifier.predict(X_test)

        total = len(self.train_data) + len(self.test_data)
        test_pct = (len(self.test_data) * 100) / total
        train_pct = 100 - test_pct

        logger.info(f"Train set: {train_pct:.1f}%")
        logger.info(f"Test set: {test_pct:.1f}%")

        try:
            self.accuracy = round(metrics.accuracy_score(y_test, y_pred), 6)
            logger.info(f"Accuracy: {self.accuracy}")
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")

    def predict_from_image(self, image_path: str) -> Tuple[np.ndarray, str]:
        """Predict faces in an image and draw results."""
        if self.classifier is None:
            raise ValueError("Classifier not trained or loaded")

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

    def predict_from_webcam(self, frame: np.ndarray) -> Tuple[np.ndarray, int, str]:
        """Predict faces in a webcam frame and draw results."""
        if self.classifier is None:
            raise ValueError("Classifier not trained or loaded")

        face_locations = face_recognition.face_locations(frame)

        if not face_locations:
            self.counter_frame = 0
            return frame, self.counter_frame, ""

        face_encodings = face_recognition.face_encodings(frame)
        predictions = [
            (self.predict(enc), loc) for enc, loc in zip(face_encodings, face_locations)
        ]

        return self._draw_predictions_on_webcam(frame, predictions)

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

    def _draw_predictions_on_webcam(self, frame: np.ndarray, predictions: List) -> Tuple[
        np.ndarray, int, str]:
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
