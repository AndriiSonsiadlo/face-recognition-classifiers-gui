# Copyright (C) 2021 Andrii Sonsiadlo

from kivy.uix.popup import Popup


class InfoPopup(Popup):
	def __init__(self, text: str, **kwargs):
		super().__init__(**kwargs)
		self.title = text

	def ok_pressed(self):
		self.dismiss()
