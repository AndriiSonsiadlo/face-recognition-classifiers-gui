# Copyright (C) 2021 Andrii Sonsiadlo

from model.model_list import ModelList
from person.person_list import PersonList
from ui.popups.ask import AskPopup


class DeletePersonPopup(AskPopup):
    def __init__(self, **kwargs):
        super().__init__(text="Are you sure you want to delete '" + self.selected.name + "'?",
                         **kwargs)
        self.list = PersonList()
        self.selected = self.list.get_selected()

    def yes_pressed(self):
        self.list.delete_person(self.selected.name)
        super().yes_pressed()


class DeleteModelPopup(AskPopup):
    def __init__(self, **kwargs):
        super().__init__(text="Are you sure you want to delete '" + self.selected.name + "'?",
                         **kwargs)
        self.list = ModelList()
        self.selected = self.list.get_selected()

    def yes_pressed(self):
        self.list.delete_model(self.selected.name)
        super().yes_pressed()
