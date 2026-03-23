import sys
import datetime

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from core.keyboard_manager import keyboard_manager
from core.navigator import navigator

from screens import idle_screen
from screens import greeting_screen
from screens import teacher_select
from screens import evaluation
from screens import elaborate
from screens import engage
from screens import explain
from screens import explore
from screens import kinestatic

app = QApplication(sys.argv)
main_window = QMainWindow()
main_window.setWindowTitle("Akshi Robot Interface")
main_window.setMinimumSize(900, 600)

stack = QStackedWidget()
main_window.setCentralWidget(stack)

# Bind the stack to the navigator
navigator.set_stack(stack)

# Setup Global Keyboard Manager
def global_key_press(event):
    keyboard_manager.handle_key_press(event)
    
main_window.keyPressEvent = global_key_press

# Load all instantiated screens
print("Loading screens...")
screens = {
    "idle": idle_screen.get_ui(),
    "greeting": greeting_screen.get_ui(),
    "teacher_select": teacher_select.get_ui(),
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