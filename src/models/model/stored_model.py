import os
import json
from models.model.model_metadata import ModelMetadata

class StoredModel:
    def __init__(self, directory: str):
        self.dir = directory
        self.json_path = os.path.join(directory, "metadata.json")

        with open(self.json_path, "r") as f:
            self.metadata = ModelMetadata(**json.load(f))

    def save(self):
        with open(self.json_path, "w") as f:
            json.dump(self.metadata.dict(), f, indent=4)

    @property
    def name(self):
        return self.metadata.name

    @property
    def selected(self):
        return self.metadata.selected

    def set_selected(self, value: bool):
        self.metadata.selected = value
        self.save()
