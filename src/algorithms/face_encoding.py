from typing import Tuple

import numpy as np


class FaceEncoding:
    """Represents a face encoding with its label."""

    def __init__(self, encoding: np.ndarray, name: str):
        self.encoding = encoding
        self.name = name

    def to_tuple(self) -> Tuple[np.ndarray, str]:
        return (self.encoding, self.name)
