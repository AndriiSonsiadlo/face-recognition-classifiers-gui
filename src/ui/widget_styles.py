# Copyright (C) 2021 Andrii Sonsiadlo

from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox


class RoundButton(Button):
    pass


class CustomRadioButtonStatic(CheckBox):
    opacity = 0.8

    def on_touch_down(self, *args):
        if self.active:
            return
        super(CustomRadioButtonStatic, self).on_touch_down(*args)


class CustomRadioButtonToggle(CheckBox):
    opacity = 0.8

    def on_touch_down(self, *args):
        super(CustomRadioButtonToggle, self).on_touch_down(*args)
