#!/usr/bin/env python3
"""
👋 Greeting Screen Preview Tool
===============================
Standalone tool to jump directly into the new Greeting Screen
with the welcome image background.

Usage:
    python test_greeting.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

import core.state_manager as sm
import core.navigator as nav

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("👋 Ginglu Greeting Preview")
        self.setFixedSize(1280, 720)

        # Create the Stacked Widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Initialize the navigator
        nav.navigator.set_stack(self.stack)

        # Register and show the greeting screen
        from screens import greeting_screen
        greeting_widget = greeting_screen.get_ui()
        nav.navigator.register_screen("greeting", greeting_widget)
        
        # Jump directly to it
        nav.navigator.navigate_to("greeting")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Mock some basic session logic state to prevent crashes
    import core.session_logic as session_logic
    # Override next_student to just exit for this test
    session_logic.next_student = lambda: print("Test Complete: Would move to student call.") or QTimer.singleShot(1000, app.quit)
    
    from PySide6.QtCore import QTimer
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())
