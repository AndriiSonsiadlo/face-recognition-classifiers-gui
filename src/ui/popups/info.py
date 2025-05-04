# Copyright (C) 2021 Andrii Sonsiadlo

from kivy.uix.popup import Popup


class InfoPopup(Popup):
    def __init__(self, title: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title

    def ok_pressed(self):
        self.dismiss()
