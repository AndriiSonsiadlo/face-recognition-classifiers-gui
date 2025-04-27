# Copyright (С) 2021 Andrii Sonsiadlo

import csv
import os
import shutil
import threading
import tkinter as tk
from os import path
from tkinter import filedialog

import cv2
import matplotlib.pyplot as plt
import numpy as np
from kivy.core.image import Texture
from matplotlib.ticker import MaxNLocator

from algorithms.knn_classifier import KNNClassifier
from algorithms.svm_classifier import SVMClassifier
from core import config
from model.model_list import ModelList
from person.person import Person
from person.person_list import PersonList
from ui.base_screen import BaseScreen
from ui.popups.person_info import PersonInfoPopup
from ui.popups.warn import WarnPopup
from ui.popups.plot import PlotPopup
from ui.screens.face_scanner.webcamera import WebCamera
from utils.get_time import getTime

face_scanner_screen = None


class FaceScanner(BaseScreen):
    loaded_image = None
    model_name = "N/A"
    camera_selected = ""

    LOADED = 0x1
    UNLOADED = 0x0
    photo_status = UNLOADED

    def __init__(self, **kw):
        super().__init__(**kw)

        self.model_load_list()
        self.person_load_list()

        try:
            if path.exists(config.paths.TEMP_DIR):
                shutil.rmtree(config.paths.TEMP_DIR)
            os.mkdir(config.paths.TEMP_DIR)

            if not os.path.exists(config.stats.FILE_STATS_CSV):
                open(config.stats.FILE_STATS_CSV, 'tw', encoding='utf-8').close()

        except BaseException:
            pass

    def refresh(self):  # update screen
        self.ids.number_people_database_text.text = self.set_text_number_in_base()
        self.model_list = ModelList()
        self.ids.model_name.values = self.get_values_model()

        self.person_list.get_list()

    def camera_on_off(self):
        thread = threading.Thread(target=self.toggle_camera, daemon=True)
        thread.start()

    def toggle_camera(self):
        if self.photo_status:
            self.clear_photo()
        self.person_list.read_from_file()
        self.disable_button(self.ids.identification_btn)
        WebCamera.on_off(self.ids.camera, self, self.model_list.get_selected(),
                         self.camera_selected)

    def clear_photo(self):
        self.photo_status = self.UNLOADED
        self.ids.load_image_btn.text = config.ui.TEXTS["load_photo"]
        WebCamera.clear_texture(self.ids.camera)

    def load_photo(self):
        if self.photo_status:
            self.clear_photo()
            self.disable_button(self.ids.identification_btn)
            return

        root = tk.Tk()
        root.withdraw()

        # setting extensions for searching images in explorer
        photo_paths = filedialog.askopenfilenames(filetypes=[("Image files", ".jpeg .jpg .png")])
        if photo_paths:
            # every photo is checking, then path is adding to a list of photos
            for img in photo_paths:
                img_path_lower = img.lower()
                if not os.path.isfile(img_path_lower) or os.path.splitext(img_path_lower)[1][
                    1:] not in config.person.ALLOWED_EXTENSIONS:
                    raise Exception("Invalid image path: {}".format(img_path_lower))

                model = self.model_list.get_selected()
                if model is None:
                    continue
                elif model.algorithm == config.model.ALGORITHM_KNN:
                    algorithm = KNNClassifier(model, model.path_file_model)
                elif model.algorithm == config.model.ALGORITHM_SVM:
                    algorithm = SVMClassifier(model, model.path_file_model)
                else:
                    continue

                is_loaded = algorithm.load_model()
                if is_loaded:
                    frame, name = algorithm.predict_image(img)

                    buf1 = cv2.flip(frame, 0)
                    buf = buf1.tostring()
                    image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]),
                                                   colorfmt="rgb")
                    image_texture.blit_buffer(buf, colorfmt="rgb", bufferfmt="ubyte")

                    WebCamera.set_texture(self.ids.camera, image_texture)
                    print(name)
                    if name.lower() == config.ui.TEXTS["unknown"].lower():
                        self.disable_button(button=self.ids.identification_btn)
                    else:
                        self.enable_button(button=self.ids.identification_btn, name=name)

                    self.ids.load_image_btn.text = config.ui.TEXTS["clear_photo"]
                    self.photo_status = self.LOADED
                else:
                    return

        self.get_root_window().raise_window()

    # get names of the model dropdown menu
    def get_values_model(self):
        values = []

        if self.model_list.is_empty():
            values.append("N/A")
            self.ids.number_people_model_text.text = "N/A"
            self.ids.model_name.text = values[0]
        else:
            for item in self.model_list.get_list():
                values.append(item.name)
            model = self.model_list.get_selected()
            if model is None:  # show last model if none has been selected
                model = self.model_list.get_list()[-1]
                self.model_list.set_selected(model.name)
            self.set_model_data(model)
        return values

    def set_text_camera_spinner(self):
        self.camera_selected = config.CAMERA_PORTS[0]
        return self.camera_selected

    def on_spinner_camera_select(self, camera):
        self.camera_selected = camera

    def get_values_camera(self):
        if config.CAMERA_PORTS:
            return config.CAMERA_PORTS
        else:
            return ["N/A"]

    def on_spinner_model_select(self, name):
        model = self.model_list.find_first(name)
        if model is not None:
            self.model_list.set_selected(model.name)
            self.set_model_data(model)

    def set_model_data(self, model):
        self.ids.model_name.text = model.name
        self.ids.number_people_model_text.text = str(model.count_train_Y)
        print("Loaded model:", model.name, model.created, model.author, model.comment,
              model.path_model_data)

    def model_load_list(self):
        self.model_list = ModelList()
        self.model_list.update_model_list()

    def person_load_list(self):
        self.person_list = PersonList()
        self.person_list.update_person_list()

    def set_text_number_in_base(self):

        # self.person_list.update_person_list()
        # self.person_list.read_from_file()
        return str(len(PersonList().get_list()))

    def switch_on_person(self, name):
        if (WebCamera.get_status_camera(self.ids.camera)):
            WebCamera.clock_unshedule(self.ids.camera)

        person = self.person_list.find_first(name)
        if person is not None:
            self.show_popup_person_info(person=person)
        else:
            self.show_popup_warm(title=f"{name} not found in database")

    def show_popup_warm(self, title):
        WarnPopup(text=title).open()

    def show_popup_person_info(self, person: Person):
        PersonInfoPopup(person=person).open()

    def disable_button(self, button):
        if button == self.ids.identification_btn:
            button.text = config.ui.TEXTS["no_elements"]
            self.disable_button(self.ids.its_ok_btn)
            self.disable_button(self.ids.its_nok_btn)

        button.disabled = True
        button.opacity = .5

    def enable_button(self, button, name=''):
        if button == self.ids.identification_btn:
            button.text = name
            self.enable_button(button=self.ids.its_ok_btn)
            self.enable_button(button=self.ids.its_nok_btn)
            self.its_add_one()
        button.disabled = False
        button.opacity = 1

    def read_plot(self):
        data_csv = []
        if os.path.exists(config.stats.FILE_STATS_CSV):
            with open(config.stats.FILE_STATS_CSV, 'r') as csvfile:
                file_rd = csv.reader(csvfile, delimiter=',')
                for (i, row) in enumerate(file_rd):
                    data_csv.append(row)
        else:
            self.clear_stats()
            return config.stats.FILE_RESULT_PLOT

        try:
            len1 = len(data_csv[0])
        except Exception:
            self.clear_stats()
            return config.stats.FILE_RESULT_PLOT

        if (len1):
            current_hour = int(getTime("hour"))
            current_day = int(getTime("day"))
            current_month = int(getTime("month"))

            range_hours = []
            range_day = []

            if (current_hour - 11) < 0:
                first_hour = 24 - (11 - current_hour)
                range_day.append(current_day - 1)
                range_day.append(current_day)
            else:
                first_hour = current_hour - 11
                range_day.append(current_day)

            #			with open(path_file_stats, "a", newline='') as gen_file:
            #				writing = csv.writer(gen_file, delimiter=',')
            #				data = [current_hour, current_day, current_month, 0, 0, 0]
            #				writing.writerow(data)

            for hour in range(12):
                if (first_hour + hour > current_hour) and (first_hour + hour < 24):
                    range_hours.append(first_hour + hour)
                elif first_hour + hour >= 24:
                    range_hours.append((first_hour + hour) - 24)
                else:
                    range_hours.append(first_hour + hour)

            x = []
            ok_y = []
            nok_y = []
            nnok_y = []

            for hour in range_hours:
                ok = 0
                nok = 0
                nnok = 0

                for element2 in data_csv:
                    if int(element2[0]) == hour and int(element2[1]) in range_day:
                        nnok += int(element2[3])
                        ok += int(element2[4])
                        nok += int(element2[5])
                x.append(hour)
                if nnok - nok - ok < 0:
                    nnok_y.append(0)
                else:
                    nnok_y.append(nnok - nok - ok)
                nok_y.append(nok)
                ok_y.append(ok)

            # for element1 in data_csv:
            # 	hour = int(element1[0])
            # 	day = int(element1[1])
            # 	month = int(element1[2])
            #
            # 	if (not hour in black_list) and (hour in range_hours) and (day in range_day) and (month == current_month):
            # 		black_list.append(hour)
            # 		ok = 0
            # 		nok = 0
            # 		nnok = 0
            #
            # 		for element2 in data_csv:
            # 			if int(element2[0]) == int(hour):
            # 				nnok += int(element2[3])
            # 				ok += int(element2[4])
            # 				nok += int(element2[5])
            # 		x.append(hour)
            # 		if nnok-nok-ok < 0:
            # 			nnok_y.append(0)
            # 		else:
            # 			nnok_y.append(nnok-nok-ok)
            # 		nok_y.append(nok)
            # 		ok_y.append(ok)

            series1 = np.array(ok_y)
            series2 = np.array(nok_y)
            series3 = np.array(nnok_y)

            index = np.arange(len(x))
            plt.title('Result of identification (per hour)')
            plt.ylabel('Count of identificated')
            plt.xlabel('Hour')

            plt.bar(index, series1, color="g")
            plt.bar(index, series2, color="r", bottom=series1)
            plt.bar(index, series3, color="b", bottom=(series2 + series1))
            # plt.tight_layout()
            plt.xticks(index, x)
            ax = plt.gca()
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.grid(axis='y')
            plt.savefig(config.stats.FILE_RESULT_PLOT)
            plt.clf()

            self.update_right_plot(config.stats.FILE_RESULT_PLOT)
        else:
            self.clear_stats()

            self.update_right_plot(config.stats.FILE_RESULT_PLOT)
        return str(config.stats.FILE_RESULT_PLOT)

    def clear_stats(self):
        current_hour = int(getTime("hour"))
        current_day = int(getTime("day"))
        current_month = int(getTime("month"))

        range_hours = []

        if (current_hour - 11) < 0:
            first_hour = 24 - current_hour - 11

        else:
            first_hour = current_hour - 11

        for hour in range(12):
            range_hours.append(first_hour + hour)

        with open(config.stats.FILE_STATS_CSV, "w", newline='') as gen_file:
            writing = csv.writer(gen_file, delimiter=',')
            for hour in range_hours:
                if hour > current_hour:
                    data = [hour, current_day - 1, current_month, 0, 0, 0]
                    writing.writerow(data)
                else:
                    data = [hour, current_day, current_month, 0, 0, 0]
                    writing.writerow(data)

        plt.title('Result of identification (per hour)')
        plt.ylabel('Count of identificated')
        plt.xlabel('Hour')
        plt.xticks(np.arange(len(range_hours)), range_hours)
        ax = plt.gca()
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(axis='y')
        plt.savefig(config.stats.FILE_RESULT_PLOT)
        plt.clf()
        self.read_plot()

    def popup_photo(self):
        if (os.path.exists(config.stats.FILE_RESULT_PLOT)):
            try:
                popup_window = PlotPopup(self.ids.plot.source)
                popup_window.open()
                pass
            except BaseException:
                pass

    def update_right_plot(self, source):
        self.ids.plot.source = str(source)
        self.ids.plot.reload()

    def its_ok(self):
        self.disable_button(button=self.ids.its_ok_btn)
        self.disable_button(button=self.ids.its_nok_btn)

        current_hour = int(getTime("hour"))
        current_day = int(getTime("day"))
        current_month = int(getTime("month"))
        data = [current_hour, current_day, current_month, 0, 1, 0]

        with open(config.stats.FILE_STATS_CSV, "a", newline='') as gen_file:
            writing = csv.writer(gen_file, delimiter=',')
            writing.writerow(data)
        self.read_plot()

    def its_nok(self):
        self.disable_button(button=self.ids.its_ok_btn)
        self.disable_button(button=self.ids.its_nok_btn)

        current_hour = int(getTime("hour"))
        current_day = int(getTime("day"))
        current_month = int(getTime("month"))

        data = [current_hour, current_day, current_month, 0, 0, 1]

        with open(config.stats.FILE_STATS_CSV, "a", newline='') as gen_file:
            writing = csv.writer(gen_file, delimiter=',')
            writing.writerow(data)
        self.read_plot()

    def its_add_one(self):
        current_hour = int(getTime("hour"))
        current_day = int(getTime("day"))
        current_month = int(getTime("month"))

        data = [current_hour, current_day, current_month, 1, 0, 0]

        with open(config.stats.FILE_STATS_CSV, "a", newline='') as gen_file:
            writing = csv.writer(gen_file, delimiter=',')
            writing.writerow(data)
        self.read_plot()
