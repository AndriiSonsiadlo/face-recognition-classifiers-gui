from datetime import datetime
from typing import Optional

from pydantic import BaseModel, NonNegativeInt, NonNegativeFloat


class ModelMetadata(BaseModel):
    name: str
    author: str
    comment: str = ""
    created_at: datetime = datetime.now()
    learning_time: NonNegativeInt

    algorithm: str
    accuracy: NonNegativeFloat
    threshold: NonNegativeFloat

    n_neighbors: Optional[NonNegativeInt] = None
    weight: Optional[str] = None
    gamma: Optional[str] = None

    train_dataset_Y: Optional[list] = None
    test_dataset_Y: Optional[list] = None
    count_train_Y: NonNegativeInt = 0
    count_test_Y: NonNegativeInt = 0

    selected: bool = False
