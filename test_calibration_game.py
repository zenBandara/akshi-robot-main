#!/usr/bin/env python3
"""
🎮 Calibration Game Preview
============================
Standalone test to preview all 3 acts of the calibration game
without needing Firebase or the full app flow.

Usage:
    python test_calibration_game.py

Controls:
    1 → Init scene
    2 → Owl Eyes (eyes open)
    3 → Sleeping Bunny (eyes closed)
    4 → Celebration (done)
    Space → Auto-play full calibration flow
    Q → Quit
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from components.calibration_game import CalibrationGameWidget


class PreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 Akshi Calibration Game — Preview")
        self.setMinimumSize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Game widget
        self.game = CalibrationGameWidget()
        layout.addWidget(self.game)

        # Controls hint
        hint = QLabel("  Keys: [1] Init  [2] Owl  [3] Bunny  [4] Celebrate  [Space] Auto-play  [Q] Quit")
        hint.setFixedHeight(30)
        hint.setStyleSheet("background: #1a1a2e; color: #aaa; font-size: 12px; padding-left: 10px;")
        layout.addWidget(hint)

        # Auto-play state
        self.auto_frame = 0
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self._auto_tick)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_1:
            self.auto_timer.stop()
            self.game.reset()
            self.game.set_phase("init")
            print("→ Init scene")
        elif key == Qt.Key_2:
            self.auto_timer.stop()
            self.game.set_phase("open")
            self.game.update_progress(50, 200)
            print("→ Owl Eyes scene")
        elif key == Qt.Key_3:
            self.auto_timer.stop()
            self.game.set_phase("closed")
            self.game.update_progress(150, 200)
            print("→ Sleeping Bunny scene")
        elif key == Qt.Key_4:
            self.auto_timer.stop()
            self.game.set_phase("done")
            print("→ Celebration scene")
        elif key == Qt.Key_Space:
            print("→ Auto-play starting...")
            self.game.reset()
            self.game.set_phase("init")
            self.auto_frame = 0
            self.auto_timer.start(100)  # 10 Hz like the real server
        elif key == Qt.Key_Q:
            self.close()

    def _auto_tick(self):
        self.auto_frame += 1
        total = 200

        if self.auto_frame <= 10:
            # Init phase for 1 second
            self.game.set_phase("init")
        elif self.auto_frame <= 10 + total // 2:
            # Eyes open
            frame = self.auto_frame - 10
            self.game.set_phase("open")
            self.game.update_progress(frame, total)
        elif self.auto_frame <= 10 + total:
            # Eyes closed
            frame = self.auto_frame - 10
            self.game.set_phase("closed")
            self.game.update_progress(frame, total)
        elif self.auto_frame <= 10 + total + 50:
            # Celebration
            self.game.set_phase("done")
        else:
            self.auto_timer.stop()
            print("→ Auto-play complete!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PreviewWindow()
    window.show()
    sys.exit(app.exec())
