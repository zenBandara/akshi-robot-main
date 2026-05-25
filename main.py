# New branch comment for checking
import sys
import os
import signal
import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, 
    QGraphicsView, QGraphicsScene, QGraphicsProxyWidget
)
from PySide6.QtCore import QObject, QEvent, Qt, QRectF
from PySide6.QtGui import QPainter

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DISPLAY SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
# Physical screen resolution (Raspberry Pi display)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# CRITICAL BUGFIX: Core graphic resource engine MUST boot BEFORE Chromium memory allocations!
app = QApplication(sys.argv)

from core.firebase import update_connected_ip
# Upload IP address immediately on startup
update_connected_ip()

from core.keyboard_manager import keyboard_manager
from core.navigator import navigator

from screens import (
    idle_screen, greeting_screen, teacher_select, student_call_screen,
    session_complete_screen, evaluate_screen, elaborate_screen, 
    celebration_screen, engage_screen, explain_screen, explore_screen,
    teacher_intervention, break_screen, kinestatic, task_intro_screen,
    calibration_screen, water_break_screen
)

class ScalableWindow(QMainWindow):
    """
    A specialized QMainWindow that hosts a 1280x720 UI and scales it 
    down to fit the physical screen resolution (e.g., 800x480).
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jinglu Robot Interface")
        
        # 1. Create the high-res Stacked Widget (The "Brain")
        self.stack = QStackedWidget()
        self.stack.setFixedSize(TARGET_WIDTH, TARGET_HEIGHT)
        self.stack.setFocusPolicy(Qt.StrongFocus)
        
        # 2. Create the Graphics Scene to host the Stack
        self.scene = QGraphicsScene(0, 0, TARGET_WIDTH, TARGET_HEIGHT)
        self.proxy = self.scene.addWidget(self.stack)
        
        # 3. Create the View (The "Lens" that scales)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHints(
            QPainter.Antialiasing | 
            QPainter.SmoothPixmapTransform | 
            QPainter.TextAntialiasing
        )
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setFrameShape(QGraphicsView.NoFrame)
        self.view.setStyleSheet("background: black;") # Letterboxing color
        
        self.setCentralWidget(self.view)
        self.setFocusPolicy(Qt.StrongFocus)

    def resizeEvent(self, event):
        """Automatically scale the UI whenever the window size changes."""
        self.apply_scaling()
        super().resizeEvent(event)

    def apply_scaling(self):
        # Calculate scaling ratios
        view_w = self.view.width()
        view_h = self.view.height()
        
        if view_w <= 0 or view_h <= 0:
            return

        scale_x = view_w / TARGET_WIDTH
        scale_y = view_h / TARGET_HEIGHT
        
        # Use the smaller scale to maintain aspect ratio (Letterboxing)
        # Or use scale_x/scale_y directly for "stretch to fit"
        scale = min(scale_x, scale_y)
        
        self.view.resetTransform()
        self.view.scale(scale, scale)
        
        # Center the scene in the view
        self.view.setSceneRect(QRectF(0, 0, TARGET_WIDTH, TARGET_HEIGHT))

main_window = ScalableWindow()

# Setup Fullscreen Mode
main_window.setWindowFlags(Qt.FramelessWindowHint)
main_window.showFullScreen()
# Also hide the cursor for a true "Robot" feel
app.setOverrideCursor(Qt.BlankCursor)

# Bind the stack to the navigator
navigator.set_stack(main_window.stack)

# Setup Global Keyboard Manager using EventFilter
class GlobalKeyListener(QObject):
    def eventFilter(self, obj, event):
        if event.type() in [QEvent.KeyPress, QEvent.Type.KeyPress]:
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

import signal
from core import backend_manager

def cleanup_and_exit(signum, frame):
    print("\nForce quit detected. Shutting down background tracking process...")
    backend_manager.stop()
    sys.exit(0)

# Register signal handlers for robust termination (e.g. Ctrl+C)
signal.signal(signal.SIGINT, cleanup_and_exit)
signal.signal(signal.SIGTERM, cleanup_and_exit)

print("Jinglu app launched successfully!")
try:
    sys.exit(app.exec())
finally:
    # Ensure backend process is killed when the UI closes naturally
    print("Shutting down background tracking process...")
    backend_manager.stop()
