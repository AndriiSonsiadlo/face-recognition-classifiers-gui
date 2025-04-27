# Copyright (С) 2021 Andrii Sonsiadlo

import cv2
from kivy.clock import Clock, mainthread
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from kivy.properties import NumericProperty
from kivy.uix.image import Image

from algorithms.knn_classifier import KNNClassifier
from algorithms.svm_classifier import SVMClassifier
from core import config


class WebCamera(Image):
	STARTED = 0b01
	STOPPED = 0b00
	PAUSED = 0b10

	camera_port = 0
	camera_status = STOPPED

	fps = NumericProperty(30)
	_capture = None

	algorithm = None
	main_screen = None
	model = None

	def __init__(self, **kwargs):
		super(WebCamera, self).__init__(**kwargs)
		self.clear_texture()

	def __del__(self):
		if self._capture is not None:
			self._capture.release()
			self._capture = None
		cv2.destroyAllWindows()

	def get_status_camera(self):
		return self.camera_status

	def set_main_screen(self, main_screen):
		self.main_screen = main_screen

	def clear_texture(self):
		self.texture = CoreImage(config.images.camera_off_path_image).texture

	@mainthread
	def on_start(self, model):
		if not self.camera_status:
			self.camera_status = self.STARTED
			self.main_screen.ids.on_off_btn.text = config.ui.TEXTS["stop_webcam"]
			self.model = model

			if self.model is not None:
				if self.model.algorithm == config.model.ALGORITHM_KNN:
					self.algorithm = KNNClassifier(self.model, self.model.path_file_model)

				elif self.model.algorithm == config.model.ALGORITHM_SVM:
					self.algorithm = SVMClassifier(self.model, self.model.path_file_model)
				else:
					return
				is_loaded = self.algorithm.load_model()
				if not is_loaded:
					self.on_stop()
					return

			self._capture = cv2.VideoCapture(self.camera_port, cv2.CAP_DSHOW)
			Clock.schedule_interval(self.update, 1.0 / self.fps)

	@mainthread
	def on_stop(self):
		self.camera_status = self.STOPPED
		self.main_screen.ids.on_off_btn.text = config.ui.TEXTS["start_webcam"]
		if self._capture is not None:
			self.algorithm = None
			self.model = None
			self._capture.release()
			self.clear_texture()

	def on_off(self, main_screen, model, camera_name):
		self.main_screen = main_screen

		self.disable_button(self.main_screen.ids.on_off_btn)
		if self.camera_status:
			self.on_stop()
			self.enable_button(self.main_screen.ids.load_image_btn)
		else:
			self.set_camera_port(camera_name=camera_name)
			self.on_start(model=model)
			self.disable_button(self.main_screen.ids.load_image_btn)
		self.enable_button(self.main_screen.ids.on_off_btn)

	def set_camera_port(self, camera_name):
		port = camera_name.split("Port")[-1]
		if port.isnumeric():
			self.camera_port = int(port)
		else:
			self.camera_port = 0

	@mainthread
	def set_texture(self, im):
		self.texture = im

	def on_source(self, *args):
		if self._capture is not None:
			self._capture.release()
			self._capture = None
		self._capture = cv2.VideoCapture(self.camera_port)

	@property
	def capture(self):
		return self._capture

	def clock_unshedule(self):
		Clock.unschedule(self.update)

	def update(self, dt):
		ret, frame = self.capture.read()
		if ret:
			if self.model is not None:
				frame, counter_frame, name = self.algorithm.predict_webcam(frame)
				print(name)

				if (counter_frame >= config.person.DEFAULT_COUNT_FRAME) and name != config.ui.TEXTS["unknown"]:
					self.main_screen.ids.identification_btn.text = str(name)
					self.enable_button(self.main_screen.ids.identification_btn)
					# Auto stop capture
					Clock.unschedule(self.update)

				elif counter_frame < config.person.DEFAULT_COUNT_FRAME:
					self.main_screen.ids.identification_btn.text = str(config.ui.TEXTS["unknown"])
					self.disable_button(self.main_screen.ids.identification_btn)
					self.disable_button(self.main_screen.ids.its_nok_btn)
					self.disable_button(self.main_screen.ids.its_ok_btn)

			buf = cv2.flip(frame, 0).tostring()
			image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
			image_texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")

			self.set_texture(image_texture)
		else:
			if self.camera_status != self.STOPPED:
				self.camera_status = self.PAUSED
			self.clock_unshedule()
			if self.main_screen is not None:
				self.on_stop()

	def disable_button(self, button):
		button.disabled = True
		button.opacity = .5

	def enable_button(self, button):
		if (button == self.main_screen.ids.identification_btn):
			self.enable_button(button=self.main_screen.ids.its_ok_btn)
			self.enable_button(button=self.main_screen.ids.its_nok_btn)
			self.main_screen.its_add_one()
		button.disabled = False
		button.opacity = 1
