from services import person_service, model_service
from ui.popups.ask import AskPopup


class DeletePersonPopup(AskPopup):
    def __init__(self, name: str, **kwargs):
        super().__init__(text="Are you sure you want to delete '" + name + "'?",
                         **kwargs)
        self.name = name

    def yes_pressed(self):
        person_service.delete_person(self.name)
        super().yes_pressed()


class DeleteModelPopup(AskPopup):
    def __init__(self, name: str, **kwargs):
        super().__init__(text="Are you sure you want to delete '" + name + "'?",
                         **kwargs)
        self.name = name

    def yes_pressed(self):
        model_service.delete_model(self.name)
        super().yes_pressed()
