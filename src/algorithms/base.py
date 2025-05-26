import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import face_recognition
import numpy as np
from PIL import ImageDraw, Image
from sklearn.model_selection import train_test_split

from algorithms.face_encoding import FaceEncoding
from core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class ClassifierBase(ABC):
    MAX_WORKERS = 8
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

        self.train_persons: List[str] = []
        self.test_persons: List[str] = []

    @abstractmethod
    def train(self) -> bool:
        pass

    @abstractmethod
    def predict(self, encoding: np.ndarray) -> str:
        pass

    def _load_training_data(self) -> bool:
        try:
            self.train_data.clear()
            self.test_data.clear()
            self.train_persons.clear()
            self.test_persons.clear()

            from services import person_service
            persons = person_service.get_persons_with_photos(min_photos=1)
            if not persons:
                logger.warning("No persons with photos found")
                return False

            total_encodings = 0

            for person in persons:
                person_encodings = []

                for photo_path in person.photo_paths:
                    try:
                        if not Path(photo_path).exists():
                            logger.warning(f"Photo not found: {photo_path}")
                            continue

                        image = face_recognition.load_image_file(str(photo_path))
                        face_locations = face_recognition.face_locations(image)
                        if not face_locations:
                            logger.debug(f"No faces detected in: {photo_path}")
                            continue

                        encodings = face_recognition.face_encodings(
                            image,
                            known_face_locations=face_locations
                        )

                        for encoding in encodings:
                            person_encodings.append(
                                FaceEncoding(encoding=encoding, name=person.name)
                            )
                            total_encodings += 1

                    except Exception as e:
                        logger.warning(f"Error processing photo {photo_path}: {e}")
                        continue

                # split person's encodings into train/test
                if len(person_encodings) > 0:
                    if len(person_encodings) >= 2:
                        # 80/20 split
                        train, test = train_test_split(
                            person_encodings,
                            test_size=0.2,
                            random_state=42
                        )
                        self.train_data.extend(train)
                        self.test_data.extend(test)
                    else:
                        # only 1 encoding, put in training
                        self.train_data.extend(person_encodings)

                    # track persons in training
                    if person.name not in self.train_persons:
                        self.train_persons.append(person.name)
                    if any(fe.name == person.name for fe in self.test_data):
                        if person.name not in self.test_persons:
                            self.test_persons.append(person.name)

            if not self.train_data:
                logger.error("No training data extracted from persons")
                return False

            logger.info(
                f"Loaded {total_encodings} encodings from {len(persons)} persons. "
                f"Train: {len(self.train_data)}, Test: {len(self.test_data)}"
            )
            return True

        except Exception as e:
            logger.exception(f"Error loading training data: {e}")
            return False

    def _prepare_training_data(self) -> Tuple[List, List]:
        try:
            x_train = [enc.encoding for enc in self.train_data]
            y_train = [enc.name for enc in self.train_data]
            return x_train, y_train
        except Exception as e:
            logger.exception(f"Error preparing training data: {e}")
            return [], []

    def _prepare_test_data(self) -> Tuple[List, List]:
        try:
            x_test = [enc.encoding for enc in self.test_data]
            y_test = [enc.name for enc in self.test_data]
            return x_test, y_test
        except Exception as e:
            logger.exception(f"Error preparing test data: {e}")
            return [], []

    def evaluate(self) -> None:
        try:
            if not self.test_data or self.classifier is None:
                logger.warning("Cannot evaluate: no test data or classifier")
                self.accuracy = 0.0
                return

            x_test, y_test = self._prepare_test_data()
            predictions = self.classifier.predict(x_test)
            correct = sum(1 for p, t in zip(predictions, y_test) if p == t)
            self.accuracy = correct / len(y_test) if y_test else 0.0

            logger.info(f"Model accuracy: {self.accuracy:.2%}")

        except Exception as e:
            logger.exception(f"Error evaluating model: {e}")
            self.accuracy = 0.0

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
        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_frame)

        current_name = None

        for name, (top, right, bottom, left) in predictions:
            current_name = name
            draw.rectangle(((left, top), (right, bottom)), outline=(0, 255, 0), width=2)
            draw.text((left, top - 10), str(name), fill=(0, 255, 0))

        del draw
        frame = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)

        if len(predictions) == 1 and current_name:
            if self.identified_name == current_name:
                self.counter_frame += 1
            elif current_name != self.UNKNOWN_LABEL:
                self.identified_name = current_name
                self.counter_frame = 0
        else:
            self.counter_frame = 0

        return frame, self.counter_frame, self.identified_name
