import shutil
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

from core import config, AppLogger
from ui.screen_stack import ScreenStack
from ui.screens.face_scanner.screen import FaceScanner
from ui.screens.face_scanner.webcamera_view import WebCameraView
from ui.screens.model.learn_screen import LearningMode
from ui.screens.model.edit_screen import LearningEdit
from ui.screens.model.create_screen import LearningCreate
from ui.screens.model.recycleview_create import *
from ui.screens.person.add_screen import AddPerson
from ui.screens.person.edit_screen import EditPerson
from ui.screens.person.screen import *
from ui.screens.person.recycleview import *
from ui.drop_button import DropButton
from ui.popups.delete import *
from ui.widget_styles import *

# loading ui files
Builder.load_file("assets/ui/app_ui.kv")
Builder.load_file("assets/ui/widget_styles.kv")

# screens
Builder.load_file("assets/ui/facescanner_screen.kv")
Builder.load_file("assets/ui/addperson_screen.kv")
Builder.load_file("assets/ui/editperson_screen.kv")
Builder.load_file("assets/ui/persons_screen.kv")
Builder.load_file("assets/ui/learningmode_screen.kv")
Builder.load_file("assets/ui/createmodel_screen.kv")
Builder.load_file("assets/ui/editmodel_screen.kv")

# popups
Builder.load_file("assets/ui/my_popup.kv")
Builder.load_file("assets/ui/plot_popup.kv")


class Main(GridLayout, threading.Thread):
    manager = ObjectProperty(None)


class WindowManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stack = ScreenStack()
        self.stack.add_screen("facescanner")


class Application(App):
    icon = 'assets/images/icon_pwr.ico'
    title = 'Face Recognition'

    Window.size = (800, 600)
    Window.minimum_width, Window.minimum_height = Window.size
    Window.resizable = False

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.logger = AppLogger().get_logger(__name__)

        from services import person_service, model_service
        self.person_service = person_service
        self.model_service = model_service

        self._initialize()

    def _initialize(self) -> None:
        try:
            if config.paths.TEMP_DIR.exists():
                shutil.rmtree(config.paths.TEMP_DIR)
            config.paths.TEMP_DIR.mkdir(parents=True, exist_ok=True)

            config.stats.FILE_STATS_CSV.parent.mkdir(parents=True, exist_ok=True)
            if not config.stats.FILE_STATS_CSV.exists():
                config.stats.FILE_STATS_CSV.touch()
        except Exception as e:
            self.logger.exception(f"Error initializing main app: {e}")

    def build(self):
        return Main()


if __name__ == '__main__':
    Application().run()
