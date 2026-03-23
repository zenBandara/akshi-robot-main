import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer

from core.state_manager import state_manager
from core.voice_manager import VoiceManager
from core.navigator import navigator

window = None
voice_manager = VoiceManager()

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    ui_path = os.path.join(project_root, "ui", "greetingUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    def on_show_hook():
        print("[Greeting Screen] Becoming active...")
        state_manager.set_current_screen("greeting")
        
        from core.keyboard_manager import keyboard_manager
        keyboard_manager.unregister_handler() # Prevent W spamming
        
        # Run animations & voice async after UI flips
        QTimer.singleShot(100, on_ready)

    window.on_show = on_show_hook
    return window

def on_ready():
    # Eyes open wide animation
    window.eyes_label.setText("O  O")
    
    greeting_message = "Hello there! I am Akshi! Ready to learn something fun today?"
    print(f"[Robot Speaks]: {greeting_message}")
    
    # Speak the greeting
    try:
        voice_manager.speak(greeting_message, "greeting_message")
    except Exception as e:
        print("VoiceManager error (ignoring for now):", e)

    # Wait for 3 seconds then transition to teacher selection
    QTimer.singleShot(3000, transition_to_teacher_select)

def transition_to_teacher_select():
    print("Transitioning to Teacher Select...")
    navigator.navigate_to("teacher_select")
