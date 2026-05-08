import sys
import os
import datetime

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import QObject, QEvent, Qt

# CRITICAL BUGFIX: Core graphic resource engine MUST boot BEFORE Chromium memory allocations!
app = QApplication(sys.argv)

from core.keyboard_manager import keyboard_manager
from core.navigator import navigator

from screens import idle_screen
from screens import greeting_screen
from screens import teacher_select
from screens import student_call_screen
from screens import session_complete_screen
from screens import evaluate_screen
from screens import elaborate_screen
from screens import celebration_screen
from screens import engage_screen
from screens import explain_screen
from screens import explore_screen
from screens import teacher_intervention
from screens import break_screen
from screens import kinestatic
from screens import task_intro_screen
from screens import calibration_screen
from screens import water_break_screen
main_window = QMainWindow()
main_window.setWindowTitle("Ginglu Robot Interface")
# Enforce a strict 16:9 aspect ratio natively
main_window.setFixedSize(1280, 720)
main_window.setFocusPolicy(Qt.StrongFocus) # Crucial for key events on empty windows!

stack = QStackedWidget()
stack.setFocusPolicy(Qt.StrongFocus)
main_window.setCentralWidget(stack)

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
    "evaluate": evaluate_screen.get_ui(),
    "celebration": celebration_screen.get_ui(),
    "elaborate": elaborate_screen.get_ui(),
    "engage": engage_screen.get_ui(),
    "explain": explain_screen.get_ui(),
    "explore": explore_screen.get_ui(),
    "teacher_intervention": teacher_intervention.get_ui(),
    "break": break_screen.get_ui(),
    "water_break": water_break_screen.get_ui(),
    "kinestatic": kinestatic.get_ui(),
    "task_intro": task_intro_screen.get_ui(),
    "calibration": calibration_screen.get_ui(),
}

# Register all valid screens in the navigator
for name, widget in screens.items():
    if widget:
        navigator.register_screen(name, widget)
    else:
        print(f"Warning: UI for '{name}' failed to load.")

# Set startup screen
navigator.navigate_to("teacher_select")

main_window.show()
import signal
from core import backend_manager

def cleanup_and_exit(signum, frame):
    print("\nForce quit detected. Shutting down background tracking process...")
    backend_manager.stop()
    sys.exit(0)

# Register signal handlers for robust termination (e.g. Ctrl+C)
signal.signal(signal.SIGINT, cleanup_and_exit)
signal.signal(signal.SIGTERM, cleanup_and_exit)

print("Ginglu app launched successfully!")
try:
    sys.exit(app.exec())
finally:
    # Ensure backend process is killed when the UI closes naturally
    print("Shutting down background tracking process...")
    backend_manager.stop()