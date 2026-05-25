import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Mock state manager so we have a student name for the preview
from core.state_manager import state_manager
state_manager.set_current_student("Alice")

def main():
    app = QApplication(sys.argv)

    from screens.goodbye_screen import get_ui

    w = get_ui()
    w.setWindowTitle("Preview: Goodbye Screen")
    w.resize(1280, 720)
    w.show()

    # The screen normally relies on Navigator calling on_show
    if hasattr(w, "on_show"):
        QTimer.singleShot(0, w.on_show)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
