import sys
import json
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def main():
    app = QApplication(sys.argv)

    with open('Tasks/task_jsons/t_1.json', 'r') as f:
        task_data = json.load(f)

    from screens import teacher_intervention

    w = teacher_intervention.get_ui()

    teacher_intervention.game_widget.load_data(
        student_name="Dinu",
        task_data=task_data,
        level=3,
        path=["evaluate_L1", "elaborate", "evaluate_L2", "explain",
              "evaluate_L3", "explore", "evaluate_L3", "engage",
              "evaluate_L3", "teacher_intervention"]
    )

    w.setWindowTitle("Preview: Teacher Intervention Screen")
    w.resize(1280, 720)
    w.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()