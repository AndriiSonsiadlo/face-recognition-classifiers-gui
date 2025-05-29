from kivy.uix.popup import Popup


class TrainingProgressPopup(Popup):
    def __init__(self, on_cancel_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.title = "Model is in training..."
        self.on_cancel_callback = on_cancel_callback
        self.auto_dismiss = False

    def on_cancel_pressed(self):
        try:
            if self.on_cancel_callback:
                self.on_cancel_callback()
            self.dismiss()
        except Exception as e:
            print(f"Error in cancel: {e}")

    def dismiss(self, *args, **kwargs):
        super().dismiss(*args, **kwargs)
