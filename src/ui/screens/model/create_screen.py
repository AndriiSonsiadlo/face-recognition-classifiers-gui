# Copyright (C) 2021 Andrii Sonsiadlo
import os
import re
import shutil
import threading

from kivy.clock import mainthread
from kivy.uix.screenmanager import Screen

from Popup.my_popup_warn import MyPopupWarn
from Popup.plot_popup import PlotPopup
from _const._const import *
from _const._customization import *
from _const._directory import folder_models_data
from model.model import Model
from model.model_list import ModelList
from person.person_list import PersonList


class LearningCreate(Screen):
	author = ""
	comment = ""
	algorithm_selected = ''
	weight_selected = ''  # KNN
	gamma_selected = ''  # SVN
	person_list = None

	isLearning = False
	new_model = Model()

	screen = None

	def __init__(self, **kw):
		super().__init__(**kw)
		self.person_list = PersonList()
		LearningCreate.screen = self

	@mainthread
	def clear_inputs(self):
		if (self.isLearning):
			self.ids.begin_learning_button.color = normal_text_color
			self.ids.begin_learning_button.text = text_learning
		else:
			self.enable_input(False)
			self.ids.create_model_name.text = ''
			self.ids.create_author.text = ''
			self.ids.create_comment.text = ''

			self.new_model = Model()

			self.ids.begin_learning_button.disabled = False
			self.ids.begin_learning_button.opacity = .8
			self.ids.begin_learning_button.text = text_train_model
			self.ids.learning_results.opacity = 0

	def set_data_recycleview(self):
		self.ids.rv_box.select_node(None)
		self.person_list = PersonList()
		if len(self.person_list.get_list_with_photo()):
			self.ids.rv.data = [{'text': person.name} for person in PersonList().get_list_with_photo()]
		else:
			self.ids.rv.data = [{'text': no_elements_text}]

	def set_search_data_recycleview(self, person_list):
		if len(person_list):
			self.ids.rv.data = [{'text': person.name} for person in person_list]
		else:
			self.ids.rv.data = [{'text': no_elements_text}]

	def search_person(self, text_filter):
		search_person_list = []
		self.ids.rv_box.select_node(None)
		for person in self.person_list.get_list_with_photo():
			try:
				if re.search(str(text_filter).lower(), person.name.lower()):
					search_person_list.append(person)
			except BaseException:
				pass
		self.set_search_data_recycleview(search_person_list)

	def change_text(self):
		if self.ids.begin_learning_button.text == text_train_model:
			self.ids.begin_learning_button.color = normal_text_color
			self.ids.begin_learning_button.text = text_learning

	def enable_learning_btn(self):  # enables training button

		self.isLearning = False
		self.ids.begin_learning_button.disabled = False
		self.ids.begin_learning_button.text = text_train_model
		self.ids.begin_learning_button.color = normal_text_color
		self.ids.learning_results.opacity = 0

	def begin_learning(self):
		if (self.isLearning == False):
			self.isLearning = True
			threading.Thread(target=self.begin_learning_release, daemon=True).start()

	def begin_learning_release(self):
		person_list = PersonList()
		model_list = ModelList()

		if self.ids.begin_learning_button.text == text_learning:
			if len(person_list.get_list_with_photo()):
				self.new_model.name = self.ids.create_model_name.text
				self.new_model.author = self.ids.create_author.text
				self.new_model.comment = self.ids.create_comment.text

				if self.new_model.name == "":
					self.new_model.name = text_unnamed
					self.ids.create_model_name.text = self.new_model.name
				if self.new_model.author == "":
					self.new_model.author = text_unknown
					self.ids.create_author.text = self.new_model.author
				if model_list.check_name_exists(self.new_model.name):
					print("File", self.new_model.name, "already exists")
					repeated = 1
					while model_list.check_name_exists(self.new_model.name + "(" + str(repeated) + ")"):
						repeated += 1
					self.new_model.name += "(" + str(repeated) + ")"
					self.ids.create_model_name.text = self.new_model.name

				self.new_model.path_model_data = os.path.join(folder_models_data, self.new_model.name)
				if not os.path.isdir(folder_models_data):
					os.mkdir(folder_models_data)
				if not os.path.isdir(self.new_model.path_model_data):
					os.mkdir(self.new_model.path_model_data)

				if self.ids.neighbor_checkbox.active == False:
					n_neighbor = None
				else:
					try:
						n_neighbor = int(self.ids.create_neighbor_num.text)
					except BaseException:
						n_neighbor = None

				learned_succes, title_warn = self.new_model.begin_learning(algorithm=self.algorithm_selected,
				                                                           n_neighbor=n_neighbor,
				                                                           weight=self.weight_selected,
				                                                           gamma=self.gamma_selected)
				if (learned_succes):
					print(self.new_model.learning_time)

					model_list.add_model(self.new_model)
					model_list.set_selected(model_list.get_list()[-1].name)
					self.ids.begin_learning_button.text = text_completed

					self.show_results(learning_time=self.new_model.learning_time, threshold=self.new_model.threshold,
					                  accuracy=self.new_model.accuracy)

					self.ids.begin_learning_button.disabled = True
					self.ids.begin_learning_button.opacity = .5
					self.new_model = Model()
				else:
					self.show_popup_warm(title=title_warn)
					self.ids.begin_learning_button.text = text_train_model
					self.ids.begin_learning_button.color = normal_text_color
					try:
						shutil.rmtree(f"{self.new_model.path_model_data}")
					except BaseException:
						pass
			else:
				self.show_popup_warm(title="Not found persons with a photo")
		self.isLearning = False

	@mainthread
	def show_results(self, learning_time, threshold, accuracy):
		threshold = str(round(threshold, 5))
		if self.algorithm_selected == algorithm_knn:
			self.ids.learning_results.text = f"Learning time: {learning_time} s, accuracy: {accuracy}, default threshold: {threshold}"
		else:
			self.ids.learning_results.text = f"Learning time: {learning_time} s, accuracy: {accuracy}"
		self.ids.learning_results.opacity = 1

	def save_model(self):
		if self.ids.begin_learning_button.text == 'OK':
			self.ids.begin_learning_button.text = text_train_model
			self.manager.current = "learning"

	@mainthread
	def show_plot(self, data_path):
		plot_path = os.path.join(data_path, 'plot.png')
		popupWindow = PlotPopup(plot_path)
		popupWindow.open()

	def show_popup_warm(self, title):
		popupWindow = MyPopupWarn(text=title)
		popupWindow.open()

	def enable_input(self, value):
		if value is True:
			self.ids.neighbor_checkbox.active = True
			self.ids.create_neighbor_num.disabled = False
			self.ids.create_neighbor_num.text = ''
			self.ids.create_neighbor_num.hint_text = 'auto'
		else:
			self.ids.neighbor_checkbox.active = False
			self.ids.create_neighbor_num.disabled = True
			self.ids.create_neighbor_num.text = 'auto'

	def cancel_learning(self):
		print("learning canceled by user")

	def refresh(self):
		self.algorithm_selected = self.ids.spinner_algorithm.text
		self.on_spinner_select_algorithm(self.algorithm_selected)

		self.set_data_recycleview()

	def on_spinner_select_algorithm(self, algorithm):
		self.algorithm_selected = algorithm
		if self.algorithm_selected == algorithm_knn:
			self.ids.neighbor_box.height = 30
			self.ids.neighbor_box.opacity = 1
			self.ids.weights_box.height = 30
			self.ids.weights_box.opacity = 1

			self.ids.gamma_box.height = 0
			self.ids.gamma_box.opacity = 0
		else:
			self.ids.gamma_box.height = 30
			self.ids.gamma_box.opacity = 1

			self.ids.neighbor_box.height = 0
			self.ids.neighbor_box.opacity = 0
			self.ids.weights_box.height = 0
			self.ids.weights_box.opacity = 0

	def on_spinner_select_weights(self, weights):
		self.weight_selected = weights

	def on_spinner_select_gamma(self, gamma):
		self.gamma_selected = gamma

	def get_values_algorithm(self):
		if algorithms_values:
			return algorithms_values
		else:
			return []

	def get_values_weights(self):
		if weights_values:
			return weights_values
		else:
			return []

	def get_values_gamma(self):
		if gamma_values:
			return gamma_values
		else:
			return []

	def set_text_algorithm_spinner(self):
		self.algorithm_selected = algorithms_values[0]
		return self.algorithm_selected

	def set_text_weights_spinner(self):
		self.weight_selected = weights_values[0]
		return self.weight_selected

	def set_text_gamma_spinner(self):
		self.gamma_selected = gamma_values[0]
		return self.gamma_selected
