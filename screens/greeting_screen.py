import os
from PySide6.QtCore import QTimer, Qt, QRectF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QPainter

from core.state_manager import state_manager
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes

class GreetingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        self.bg_path = os.path.join(project_root, "assets", "images", "greeting", "welcome.png")
        self.pixmap = QPixmap(self.bg_path) if os.path.exists(self.bg_path) else None

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if self.pixmap and not self.pixmap.isNull():
            p.drawPixmap(self.rect(), self.pixmap)
        else:
            p.fillRect(self.rect(), Qt.white)
        p.end()

window = None
voice_manager = VoiceManager()

def get_ui():
    global window
    if window is None:
        window = GreetingWidget()
        window.on_show = on_show
    return window

def on_show():
    print("[Greeting Screen] Becoming active with full-screen welcome image...")
    state_manager.set_current_screen("greeting")
    
    from core.keyboard_manager import keyboard_manager
    keyboard_manager.unregister_handler() 
    
    QTimer.singleShot(100, on_ready)

def on_ready():
    get_robot_eyes().set_expression("encouraging")
    greeting_message = "Hello there! I am Ginglu! Ready to learn something fun today?"
    print(f"[Robot Speaks]: {greeting_message}")
    
    duration_ms = 3000
    try:
        duration_ms = voice_manager.speak(greeting_message, "greeting_message")
    except Exception as e:
        print("VoiceManager error:", e)

    QTimer.singleShot(duration_ms, transition_to_first_student)

def transition_to_first_student():
    get_robot_eyes().set_expression("default")
    print("Transitioning to first student...")
    import core.session_logic as session_logic
    session_logic.next_student()
