from typing import Optional

import numpy as np
from pydantic import BaseModel, NonNegativeInt


class Prediction(BaseModel):
    name: str
    confidence: float
    frame: Optional[np.ndarray] = None
    counter: NonNegativeInt = 0

    class Config:
        arbitrary_types_allowed = True
