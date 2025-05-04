from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup

class PopupBox(Popup):
    pop_up_text = ObjectProperty()

    def update_pop_up_text(self, message):
        self.pop_up_text.text = message