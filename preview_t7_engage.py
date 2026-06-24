import sys
import json
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def main():
    app = QApplication(sys.argv)

    # Mock State
    from core.state_manager import state_manager
    
    with open('Tasks/task_jsons/task7.json', 'r') as f:
        task_data = json.load(f)
        
    state_manager.set_current_task(task_data)
    state_manager.set_affordance_level(1)
    state_manager.set_current_student("Dinu")

    # Import the UI
    from screens.engage_screen import get_ui

    w = get_ui()
    w.setWindowTitle("Preview: Engage Screen - Colors")
    w.setFixedSize(1280, 720)
    w.show()

    if hasattr(w, "on_show"):
        QTimer.singleShot(0, w.on_show)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()