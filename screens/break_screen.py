import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "breakUI.ui")

window = None
input_enabled = False

def get_ui():
    global window
    if window is None:
        loader = QUiLoader()
        file = QFile(ui_path)
        if not file.open(QFile.ReadOnly):
            print("Cannot open UI file:", ui_path)
            return None
        window = loader.load(file)
        file.close()
        
        window.on_show = on_show
        
    return window

def on_show():
    global input_enabled
    print("[Break Screen] Becoming active...")
    state_manager.set_current_screen("break")
    
    # Simple robot voice output stub
    print("🤖 ROBOT SPEAKS: \"Take your time! Press Enter when you're ready to come back.\"")
    
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action == "ENTER": # Mapped natively inside keyboard_manager.py
        input_enabled = False
        print("[Break Screen] Student pressed Enter. Resuming Evaluate Session...")
        
        try:
            from screens import evaluate_screen
            parent_stack = window.parentWidget()
            if parent_stack:
                evaluate_ui = evaluate_screen.get_ui()
                parent_stack.addWidget(evaluate_ui)
                parent_stack.setCurrentWidget(evaluate_ui)
        except ImportError:
            print("Warning: Could not transition back to evaluate screen.")
