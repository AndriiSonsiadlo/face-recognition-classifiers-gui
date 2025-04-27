# Copyright (C) 2021 Andrii Sonsiadlo

import re
from kivy.uix.screenmanager import Screen
from Popup.my_popup_ask import MyPopupAskModel
from _const._const import algorithm_knn
from _const._customization import no_elements_text
from model.model_list import ModelList
from person.person_list import PersonList


class LearningMode(Screen):
	model_name = "N/A"
	created = "N/A"
	author = "N/A"
	comment = "N/A"
	model_list: ModelList

	def __init__(self, **kw):
		super().__init__(**kw)
		self.load_list()

	def refresh(self):  # update screen
		self.ids.model_name.values = self.get_values()
		self.ids.rv_box.select_node(None)
		self.show_selected()

	def load_list(self):
		self.model_list = ModelList()
		self.model_list.update_model_list()

	# display model info on screen
	def set_model_data(self, name):
		model = self.model_list.find_first(name)
		self.model_list.set_selected(name)
		self.ids.model_name.text = model.name
		self.ids.created_date.text = model.created
		self.ids.author.text = model.author
		self.ids.comment.text = model.comment
		if model.comment != '':
			self.ids.comment.opacity = 1
		else:
			self.ids.comment.opacity = 0

		self.ids.algorithm_text.text = model.algorithm
		if (model.algorithm == algorithm_knn):
			self.ids.neighbor_box.height = 30
			self.ids.neighbor_box.opacity = 1
			self.ids.threshold_box.height = 30
			self.ids.threshold_box.opacity = 1
			self.ids.weight_box.height = 30
			self.ids.weight_box.opacity = 1

			self.ids.gamma_box.height = 0
			self.ids.gamma_box.opacity = 0

			self.ids.threshold.text = str(model.threshold)
			self.ids.num_neighbors.text = str(model.n_neighbors)
			self.ids.weight.text = str(model.weight)

		else:
			self.ids.gamma_box.height = 30
			self.ids.gamma_box.opacity = 1
			self.ids.gamma.text = str(model.gamma)

			self.ids.neighbor_box.height = 0
			self.ids.neighbor_box.opacity = 0
			self.ids.threshold_box.height = 0
			self.ids.threshold_box.opacity = 0
			self.ids.weight_box.height = 0
			self.ids.weight_box.opacity = 0

		self.ids.learning_time.text = str(model.learning_time)
		self.ids.accuracy.text = str(model.accuracy)
		self.ids.num_trained.text = str(model.count_train_Y)
		self.ids.num_tested.text = str(model.count_test_Y)
		self.ids.num_all.text = str(len(PersonList().get_list()))

		self.set_data_recycleview()
		print("Loaded model:", model.name, model.created, model.author, model.comment, model.path_model_data)

	# clear on screen model info
	def clear_model_data(self):
		self.ids.model_name.text = "N/A"
		self.ids.created_date.text = "N/A"
		self.ids.author.text = "N/A"
		self.ids.comment.text = "N/A"
		self.ids.algorithm_text.text = "N/A"
		self.ids.learning_time.text = "N/A"
		self.ids.accuracy.text = "N/A"
		self.ids.num_trained.text = "N/A"
		self.ids.num_tested.text = "N/A"
		self.ids.num_all.text = "N/A"

		self.ids.num_neighbors.text = "N/A"
		self.ids.weight.text = "N/A"
		self.ids.threshold.text = "N/A"

		self.ids.gamma_box.height = 0
		self.ids.gamma_box.opacity = 0
		self.ids.neighbor_box.height = 0
		self.ids.neighbor_box.opacity = 0
		self.ids.weight_box.height = 0
		self.ids.weight_box.opacity = 0
		self.ids.threshold_box.height = 0
		self.ids.threshold_box.opacity = 0

		self.ids.comment.opacity = 0
		self.ids.train_dataset.opacity = 0

	# get names of the model dropdown menu
	def get_values(self):
		values = []
		self.load_list()
		if self.model_list.is_empty():
			values.append("N/A")
		else:
			for item in self.model_list.get_list():
				values.append(item.name)
		return values

	def on_spinner_select(self, name):
		model = self.model_list.find_first(name)
		if model is not None:
			self.ids.rv_box.select_node(None)
			model_name = model.name
			self.model_list.set_selected(model_name)
			self.set_model_data(model_name)

	# show info about selected model
	def show_selected(self):
		if not self.model_list.is_empty():
			self.enable_button(self.ids.edit_btn)
			self.enable_button(self.ids.delete_btn)

			model = self.model_list.get_selected()
			if model is None:  # show last model if none has been selected
				model = self.model_list.get_list()[-1]
			model_name = model.name
			self.set_model_data(model_name)
			self.set_data_recycleview()
		else:
			self.clear_model_data()
			self.disable_button(self.ids.edit_btn)
			self.disable_button(self.ids.delete_btn)

	def set_data_recycleview(self):
		model = self.model_list.get_selected()
		if (model is not None):
			if len(model.train_dataset_Y):
				self.ids.train_dataset.opacity = 1
				self.ids.rv.data = [{'text': name} for name in model.train_dataset_Y]
			else:
				self.ids.rv.data = [{'text': no_elements_text}]

	def set_search_data_recycleview(self, search_list):
		if len(search_list):
			self.ids.rv.data = [{'text': name} for name in search_list]
		else:
			self.ids.rv.data = [{'text': no_elements_text}]

	def search_person(self, text_filter):
		self.ids.rv_box.select_node(None)
		model = self.model_list.get_selected()
		if (model is not None):
			search_person_list = []
			for name in model.train_dataset_Y:
				try:
					if re.search(str(text_filter).lower(), name.lower()):
						search_person_list.append(name)
				except BaseException:
					pass
			self.set_search_data_recycleview(search_person_list)

	def disable_button(self, button):
		button.disabled = True
		button.opacity = .5

	def enable_button(self, button):
		button.disabled = False
		button.opacity = 1

	def show_popup(self):
		selected = self.model_list.get_selected()
		if selected is not None:
			popupWindow = MyPopupAskModel()
			popupWindow.bind(on_dismiss=self.popup_refresh)
			popupWindow.open()

	def popup_refresh(self, instance):  # update screen after pressing delete
		self.ids.rv_box.select_node(None)
		self.load_list()
		self.refresh()
