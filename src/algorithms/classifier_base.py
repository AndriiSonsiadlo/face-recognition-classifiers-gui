"""
Required Interface for Classifier Classes
File: Reference for what KNNClassifier and SVMClassifier must implement
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, List

import numpy as np


class ClassifierInterface(ABC):
    """Abstract interface that all classifiers MUST implement.

    Your KNNClassifier and SVMClassifier must have all these methods.
    """

    # ============================================================
    # REQUIRED: Core Properties
    # ============================================================

    model_name: str
    """Name of the model/algorithm (e.g., "KNN", "SVM")"""

    model_path: Path
    """Path to save/load .clf file"""

    classifier: object
    """The underlying sklearn classifier instance"""

    accuracy: float
    """Accuracy score from test data"""

    identified_name: str
    """Last identified person name"""

    counter_frame: int
    """Number of consecutive frames with same prediction"""

    train_data: List
    """Training face encodings"""

    test_data: List
    """Test face encodings"""

    # ============================================================
    # REQUIRED: Model Lifecycle
    # ============================================================

    @abstractmethod
    def train(self) -> bool:
        """Train the classifier on data.

        Must:
        1. Load training data via _load_training_data()
        2. Prepare features/labels via _prepare_training_data()
        3. Create and fit sklearn classifier
        4. Evaluate on test set via evaluate()
        5. Save model via save_model()

        Returns:
            True if training successful

        Example:
            def train(self) -> bool:
                if not self._load_training_data():
                    return False
                x_train, y_train = self._prepare_training_data()
                self.classifier = KNeighborsClassifier(...)
                self.classifier.fit(x_train, y_train)
                self.evaluate()
                return self.save_model()
        """
        pass

    def load_model(self) -> bool:
        """Load pre-trained model from disk.

        Must:
        1. Check if file exists
        2. Unpickle the classifier
        3. Assign to self.classifier

        Returns:
            True if successful

        Implementation (you can copy this):
            def load_model(self) -> bool:
                try:
                    with open(self.model_path, 'rb') as f:
                        self.classifier = pickle.load(f)
                    logger.info(f"Model loaded from {self.model_path}")
                    return True
                except Exception as e:
                    logger.error(f"Error loading model: {e}")
                    return False
        """
        pass

    def save_model(self) -> bool:
        """Save trained model to disk as pickle.

        Must:
        1. Check if classifier exists
        2. Create directory if needed
        3. Pickle classifier to .clf file

        Returns:
            True if successful

        Implementation (you can copy this):
            def save_model(self) -> bool:
                if self.classifier is None:
                    logger.error("No classifier to save")
                    return False
                try:
                    self.model_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.model_path, 'wb') as f:
                        pickle.dump(self.classifier, f)
                    logger.info(f"Model saved to {self.model_path}")
                    return True
                except Exception as e:
                    logger.error(f"Error saving model: {e}")
                    return False
        """
        pass

    # ============================================================
    # REQUIRED: Prediction Methods
    # ============================================================

    @abstractmethod
    def predict(self, encoding: np.ndarray) -> str:
        """Predict single face encoding (low-level).

        Args:
            encoding: Face encoding from face_recognition.face_encodings()
                     Shape: (128,) for face_recognition library

        Returns:
            Person name string

        Must:
        1. Call self.classifier.predict([encoding])
        2. Return the name
        3. Handle "Unknown" if not confident

        Example (KNN):
            def predict(self, encoding: np.ndarray) -> str:
                distances, indices = self.classifier.kneighbors([encoding])
                if distances[0][0] <= self.threshold:
                    return self.classifier.predict([encoding])[0]
                else:
                    return self.UNKNOWN_LABEL

        Example (SVM):
            def predict(self, encoding: np.ndarray) -> str:
                prediction = self.classifier.predict([encoding])[0]
                return prediction
        """
        pass

    def predict_from_image(self, image_path: str) -> Tuple[np.ndarray, str]:
        """Predict from image file and draw results.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (annotated_frame, person_name)
            - annotated_frame: Image with bounding boxes and names
            - person_name: Name of person found (or "Unknown")

        Must:
        1. Load image from file
        2. Detect faces via face_recognition.face_locations()
        3. Get encodings via face_recognition.face_encodings()
        4. Predict each encoding
        5. Draw boxes and labels on image
        6. Return image and name

        This is already implemented in ClassifierBase, you inherit it.
        """
        pass

    def predict_webcam(self, frame: np.ndarray) -> Tuple[np.ndarray, int, str]:
        """Predict from video frame and draw results.

        Args:
            frame: Video frame from camera (BGR, numpy array)

        Returns:
            Tuple of (annotated_frame, counter, person_name)
            - annotated_frame: Frame with bounding boxes and names
            - counter: Consecutive frames with same person
            - person_name: Name of person (or empty string if none)

        Must:
        1. Detect faces in frame
        2. Get encodings
        3. Predict each
        4. Draw boxes and labels
        5. Track consecutive frames with same person
        6. Return frame + metadata

        Return format IMPORTANT:
            - counter increases if same person detected consecutively
            - counter resets to 0 if different person or no faces
            - Used to determine "confident identification" threshold

        This is already implemented in ClassifierBase, you inherit it.
        """
        pass

    # ============================================================
    # REQUIRED: Helper Methods (in ClassifierBase)
    # ============================================================

    def _load_training_data(self) -> bool:
        """Load training data from person directories.

        Must:
        1. Scan person_data/ directory
        2. For each person, load photos
        3. Extract face encodings
        4. Split into train/test sets
        5. Populate self.train_data and self.test_data

        Returns:
            True if data loaded successfully

        Already implemented in ClassifierBase.
        """
        pass

    def _prepare_training_data(self) -> Tuple[List, List]:
        """Prepare features and labels from train_data.

        Returns:
            Tuple of (X_train, y_train)
            - X_train: List of encodings (128-d vectors)
            - y_train: List of person names (strings)

        Example:
            X_train = [enc.encoding for enc in self.train_data]
            y_train = [enc.name for enc in self.train_data]
            return X_train, y_train
        """
        pass

    def _prepare_test_data(self) -> Tuple[List, List]:
        """Prepare features and labels from test_data.

        Returns:
            Tuple of (X_test, y_test)
        """
        pass

    def evaluate(self) -> None:
        """Evaluate classifier on test set.

        Must:
        1. Get test features/labels
        2. Make predictions
        3. Calculate accuracy score
        4. Store in self.accuracy

        Already implemented in ClassifierBase.
        """
        pass

    # ============================================================
    # REQUIRED: Drawing Methods (in ClassifierBase)
    # ============================================================

    @staticmethod
    def _load_and_resize_image(image_path: str, max_dimension: int = 400) -> np.ndarray:
        """Load and resize image to manageable size.

        Already implemented in ClassifierBase.
        """
        pass

    @staticmethod
    def _draw_predictions_on_image(
            image: np.ndarray,
            predictions: List
    ) -> Tuple[np.ndarray, str]:
        """Draw boxes and labels on static image.

        Args:
            image: Image array
            predictions: List of (name, (top, right, bottom, left)) tuples

        Returns:
            Tuple of (annotated_image, last_name)

        Already implemented in ClassifierBase.
        """
        pass

    def _draw_predictions_on_webcam(
            self,
            frame: np.ndarray,
            predictions: List
    ) -> Tuple[np.ndarray, int, str]:
        """Draw boxes on video frame and track person.

        Args:
            frame: Video frame
            predictions: List of (name, location) tuples

        Returns:
            Tuple of (annotated_frame, counter, identified_name)

        Tracks:
        - self.identified_name: Current person
        - self.counter_frame: Frames with same person

        Already implemented in ClassifierBase.
        """
        pass

    # ============================================================
    # OPTIONAL: Configuration Methods
    # ============================================================

    def set_threshold(self, threshold: float) -> None:
        """Set confidence threshold (KNN only).

        Args:
            threshold: Value between 0.0 and 1.0

        Example (KNN):
            def set_threshold(self, threshold: float) -> None:
                if not 0 <= threshold <= 1:
                    raise ValueError("Threshold must be 0-1")
                self.threshold = threshold

        Not needed for SVM.
        """
        pass


# ============================================================
# VALIDATION CHECKLIST
# ============================================================
"""
Before running FaceScanner, verify your classifier has:

For KNNClassifier:
  ✓ def __init__(model_path, n_neighbors=None, weight="distance")
  ✓ def train() -> bool
  ✓ def predict(encoding: np.ndarray) -> str
  ✓ def set_threshold(threshold: float)
  ✓ self.threshold attribute
  ✓ Inherits from ClassifierBase or has all required methods

For SVMClassifier:
  ✓ def __init__(model_path, gamma="scale")
  ✓ def train() -> bool
  ✓ def predict(encoding: np.ndarray) -> str
  ✓ Inherits from ClassifierBase or has all required methods

For Both:
  ✓ self.classifier (sklearn object)
  ✓ self.model_path (Path)
  ✓ self.accuracy (float)
  ✓ self.train_data (List[FaceEncoding])
  ✓ self.test_data (List[FaceEncoding])
  ✓ self.identified_name (str)
  ✓ self.counter_frame (int)
  ✓ def load_model() -> bool
  ✓ def save_model() -> bool
  ✓ def predict_from_image(path) -> (ndarray, str)
  ✓ def predict_webcam(frame) -> (ndarray, int, str)
  ✓ def evaluate() -> None
"""

# ============================================================
# EXAMPLE: How Your Class Should Look
# ============================================================

"""
from algorithms.classifier_base import ClassifierBase
from sklearn.neighbors import KNeighborsClassifier
import math

class KNNClassifier(ClassifierBase):
    \"\"\"Your KNN implementation.\"\"\"

    def __init__(self, model_path, n_neighbors=None, weight="distance"):
        super().__init__("KNN", model_path)
        self.n_neighbors = n_neighbors
        self.weight = weight
        self.threshold = 0.6

    def train(self) -> bool:
        \"\"\"Implement training logic.\"\"\"
        # See artifact: knn_classifier.py
        pass

    def predict(self, encoding: np.ndarray) -> str:
        \"\"\"Implement prediction logic.\"\"\"
        # See artifact: knn_classifier.py
        pass

# That's it! Everything else is inherited from ClassifierBase.
"""