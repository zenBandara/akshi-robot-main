import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QPropertyAnimation, QGraphicsOpacityEffect
from core.keyboard_manager import keyboard_manager
from core.state_manager import state_manager
from core.navigator import navigator

window = None
blink_timer = None
pulse_anim = None
fade_effect = None

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    ui_path = os.path.join(project_root, "ui", "idleUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    setup_animations()
    
    # Register keyboard handlers only when the screen becomes active
    def handle_show_event(event):
        keyboard_manager.register_handler(handle_key_press)
        state_manager.set_current_screen("idle")

    window.showEvent = handle_show_event
    return window

def setup_animations():
    global window, blink_timer, pulse_anim, fade_effect
    
    # 1. Slow glowing pulse for the hint label
    fade_effect = QGraphicsOpacityEffect(window.hint_label)
    window.hint_label.setGraphicsEffect(fade_effect)
    
    pulse_anim = QPropertyAnimation(fade_effect, b"opacity")
    pulse_anim.setDuration(2500)
    pulse_anim.setStartValue(0.2)
    pulse_anim.setKeyValueAt(0.5, 0.9)
    pulse_anim.setEndValue(0.2)
    pulse_anim.setLoopCount(-1) # Infinite loop
    pulse_anim.start()

    # 2. Occasional sleepy eye twitch representing sleeping
    def blink_eyes():
        window.eyes_label.setText(" ◡   ◡")
        QTimer.singleShot(250, lambda: window.eyes_label.setText("－  －"))
        
    blink_timer = QTimer(window)
    blink_timer.timeout.connect(blink_eyes)
    blink_timer.start(4500) # Sleep twitch every 4.5 seconds

def handle_key_press(mapped_action):
    if mapped_action == "WAKE":
        print("WAKE command triggered!")
        navigator.navigate_to("greeting")
