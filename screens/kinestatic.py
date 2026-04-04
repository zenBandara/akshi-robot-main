import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager

window = None
input_enabled = False
voice_manager = VoiceManager()

def get_ui():
    global window
    if window is None:
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        ui_path = os.path.join(project_root, "ui", "kinestaticUI.ui")

        loader = QUiLoader()
        file = QFile(ui_path)
        if hasattr(file, "open"):
            file.open(QFile.ReadOnly)
            window = loader.load(file)
            file.close()
            window.on_show = on_show
    return window

def on_show():
    print("[Kinematic Screen] Becoming active...")
    state_manager.set_current_screen("kinestatic")
    
    global input_enabled
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)
    print("Press '1' to Pass, '2' to Fail.")
    
def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action not in ["1", "2"]:
        return
        
    input_enabled = False
    print(f"[Kinematic Screen] Mock Action Received: {action}")
    
    from core.flow_controller import flow_controller
    parent_stack = window.parentWidget()
    
    if action == "1":
        print("[Kinematic Screen] Simulating PASS... 🎉")
        # Route a passing kinematic test to the normal correct handler (next steps/celebration)
        flow_controller.on_correct_answer(parent_stack)
    elif action == "2":
        print("[Kinematic Screen] Simulating FAIL... ❌")
        # Route a failing kinematic test to escalate the cascade further
        flow_controller.on_incorrect_answer(parent_stack)