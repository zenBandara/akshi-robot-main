import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile


def get_ui():

    current_dir = os.path.dirname(__file__)
    ui_path = os.path.join(current_dir, "elaborateUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    file.open(QFile.ReadOnly)

    ui = loader.load(file)
    file.close()

    return ui