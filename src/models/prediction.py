from typing import Optional

import numpy as np
from pydantic import BaseModel, NonNegativeInt


class Prediction(BaseModel):
    """Represents a face recognition prediction result."""

    name: str
    confidence: float
    frame: Optional[np.ndarray] = None
    counter: NonNegativeInt = 0

    class Config:
        arbitrary_types_allowed = True
