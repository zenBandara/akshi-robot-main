import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator

window = None

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    ui_path = os.path.join(project_root, "ui", "sessionCompleteUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    def on_show():
        print("[Session Complete Screen] Becoming active...")
        state_manager.set_current_screen("session_complete")
        keyboard_manager.register_handler(handle_key_press)
        
        # Notify backend that the student's session has historically concluded so it saves to DB
        import json
        try:
            with open("ginglu-the-robot/calibration_command.json", "w") as f:
                json.dump({"type": "end_session"}, f)
            print("Session End dispatched to backend.")
        except Exception as e:
            print("IPC Error notifying end_session:", e)

    window.on_show = on_show
    return window

def handle_key_press(mapped_action):
    # W to return to idle
    if mapped_action == "WAKE":
        print("Returning to idle...")
        navigator.navigate_to("idle")
