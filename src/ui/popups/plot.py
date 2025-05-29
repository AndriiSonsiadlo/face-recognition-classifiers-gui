import cv2
from kivy.core.image import Texture
from kivy.uix.modalview import ModalView


class PlotPopup(ModalView):
	def __init__(self, plot_path=None, texture=None, **kwargs):
		super().__init__(**kwargs)
		if texture is not None:
			buf1 = cv2.flip(texture, 0)
			buf = buf1.tostring()
			image_texture = Texture.create(size=(texture.shape[1], texture.shape[0]), colorfmt="rgb")
			image_texture.blit_buffer(buf, colorfmt="rgb", bufferfmt="ubyte")
			self.texture = image_texture
		else:
			self.ids.plot.source = plot_path

	def close(self):
		self.dismiss()
