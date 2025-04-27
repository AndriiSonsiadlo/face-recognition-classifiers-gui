import os
import json
import shutil
from typing import List
from models.model.stored_model import StoredModel
from models.model.model_metadata import ModelMetadata

class ModelRegistry:
    def __init__(self, models_root):
        self.models_root = models_root
        self.refresh()

    def refresh(self):
        """Scan directory structure and rebuild in-memory list."""
        self.models: List[StoredModel] = []

        if not os.path.isdir(self.models_root):
            os.makedirs(self.models_root)

        for dirname in os.listdir(self.models_root):
            dirpath = os.path.join(self.models_root, dirname)
            json_path = os.path.join(dirpath, "metadata.json")

            if os.path.isdir(dirpath) and os.path.isfile(json_path):
                self.models.append(StoredModel(dirpath))

    def list(self):
        return self.models

    def get(self, name: str):
        for m in self.models:
            if m.name == name:
                return m
        return None

    def add(self, meta: ModelMetadata):
        model_path = os.path.join(self.models_root, meta.name)

        if os.path.exists(model_path):
            raise ValueError("Model with this name already exists")

        os.makedirs(model_path)

        # write metadata.json
        with open(os.path.join(model_path, "metadata.json"), "w") as f:
            json.dump(meta.dict(), f, indent=4)

        self.refresh()

    def delete(self, name: str):
        m = self.get(name)
        if not m:
            return

        shutil.rmtree(m.dir)
        self.refresh()

    def rename(self, old_name, new_name):
        m = self.get(old_name)
        if not m:
            return

        new_dir = os.path.join(self.models_root, new_name)
        os.rename(m.dir, new_dir)

        m.dir = new_dir
        m.metadata.name = new_name
        m.save()

    def set_selected(self, name):
        """Only one selected model allowed."""
        for m in self.models:
            m.metadata.selected = (m.name == name)
            m.save()
