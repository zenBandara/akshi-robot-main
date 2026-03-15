import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile


def get_ui():

    current_dir = os.path.dirname(__file__)
    ui_path = os.path.join(current_dir, "evaluationUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)

    if not file.open(QFile.ReadOnly):
        print("Cannot open UI:", ui_path)
        return None

    ui = loader.load(file)
    file.close()

    return ui


def start_lesson(lesson_id):

    print("Evaluation started with lesson:", lesson_id)