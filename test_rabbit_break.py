"""
Quick preview for the Rabbit Break Widget.

Keys:
  [1] Story (Act 1)
  [2] Activity (Act 2) — starts 45s countdown
  [3] Return (Act 3) — waiting for ENTER
  [Q] Quit
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from components.rabbit_break_game import RabbitBreakWidget


class PreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🐰 Rabbit Break — Preview")
        self.setMinimumSize(900, 700)

        self.game = RabbitBreakWidget()
        self.setCentralWidget(self.game)

        # Connect signals to print
        self.game.activity_complete.connect(lambda: print(">>> SIGNAL: activity_complete"))
        self.game.halfway_reached.connect(lambda: print(">>> SIGNAL: halfway_reached"))
        self.game.almost_done.connect(lambda: print(">>> SIGNAL: almost_done"))
        self.game.return_timeout.connect(lambda: print(">>> SIGNAL: return_timeout"))
        self.game.return_warning.connect(lambda: print(">>> SIGNAL: return_warning"))

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_1:
            self.game.set_phase("story")
        elif key == Qt.Key_2:
            self.game.set_phase("activity")
        elif key == Qt.Key_3:
            self.game.set_phase("return")
        elif key == Qt.Key_Q:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PreviewWindow()
    win.show()
    print("\nKeys: [1] Story  [2] Activity  [3] Return  [Q] Quit\n")
    sys.exit(app.exec())
