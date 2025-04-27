from kivy.uix.popup import Popup


class AskPopup(Popup):
	def __init__(self, text: str, **kwargs):
		super().__init__(**kwargs)
		self.title = text

	def yes_pressed(self):
		self.dismiss()

	def no_pressed(self):
		self.dismiss()
