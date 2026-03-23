import sys
import datetime

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import QObject, QEvent, Qt

from core.keyboard_manager import keyboard_manager
from core.navigator import navigator
from components.robot_eyes import get_robot_eyes

from screens import idle_screen
from screens import greeting_screen
from screens import teacher_select
from screens import student_call_screen
from screens import session_complete_screen
from screens import evaluation
from screens import elaborate
from screens import engage
from screens import explain
from screens import explore
from screens import kinestatic

app = QApplication(sys.argv)
main_window = QMainWindow()
main_window.setWindowTitle("Akshi Robot Interface")
main_window.setMinimumSize(900, 700)
main_window.setFocusPolicy(Qt.StrongFocus) # Crucial for key events on empty windows!

stack = QStackedWidget()
stack.setFocusPolicy(Qt.StrongFocus)
main_window.setCentralWidget(stack)

# Deploy the global expressive robot face strictly bypassing the stack coordinates!
robot_eyes = get_robot_eyes()
robot_eyes.setParent(main_window)
robot_eyes.move(680, 20) # absolute float coordinate at the top right
robot_eyes.show()
robot_eyes.raise_()

# Bind the stack to the navigator
navigator.set_stack(stack)

# Setup Global Keyboard Manager using EventFilter
class GlobalKeyListener(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress or event.type() == QEvent.KeyPress:
            # print(f"Key intercepted by app filter! Key: {event.key()}") # uncomment to debug all keys
            keyboard_manager.handle_key_press(event)
            return False
        return super().eventFilter(obj, event)

key_listener = GlobalKeyListener()
app.installEventFilter(key_listener)

# Load all instantiated screens
print("Loading screens...")
screens = {
    "idle": idle_screen.get_ui(),
    "greeting": greeting_screen.get_ui(),
    "teacher_select": teacher_select.get_ui(),
    "student_call": student_call_screen.get_ui(),
    "session_complete": session_complete_screen.get_ui(),
    "evaluation": evaluation.get_ui(),
    "elaborate": elaborate.get_ui(),
    "engage": engage.get_ui(),
    "explain": explain.get_ui(),
    "explore": explore.get_ui(),
    "kinestatic": kinestatic.get_ui(),
}

# Register all valid screens in the navigator
for name, widget in screens.items():
    if widget:
        navigator.register_screen(name, widget)
    else:
        print(f"Warning: UI for '{name}' failed to load.")

# Set startup screen
navigator.navigate_to("idle")

main_window.show()
print("Akshi app launched successfully!")
sys.exit(app.exec())