#!/usr/bin/env python3
"""
👋 Goodbye Screen Preview Tool
===============================
Standalone tool to jump directly into the new Goodbye Screen
and test the 20-second loop and "BYE" keyboard mapping.

Usage:
    python test_goodbye.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt, QTimer

import core.state_manager as sm
import core.navigator as nav

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("👋 Jinglu Goodbye Preview")
        self.setFixedSize(1280, 720)

        # Create the Stacked Widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Initialize the navigator
        nav.navigator.set_stack(self.stack)

        # Mock a student name for the screen to use
        sm.state_manager.set_current_student("Alice")

        # Register and show the goodbye screen
        from screens import goodbye_screen
        goodbye_widget = goodbye_screen.get_ui()
        nav.navigator.register_screen("goodbye", goodbye_widget)
        
        # Jump directly to it
        nav.navigator.navigate_to("goodbye")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Mock next_student logic so it doesn't try to load other screens
    import core.session_logic as session_logic
    
    def fake_next_student():
        print("\n✅ SUCCESS: session_logic.next_student() was called!")
        print("The 'BYE' command successfully triggered the exit logic.")
        print("Closing the test in 2 seconds...")
        QTimer.singleShot(2000, app.quit)
        
    session_logic.next_student = fake_next_student
    
    window = TestWindow()
    window.show()
    
    print("\n" + "="*50)
    print("🧪 GOODBYE SCREEN TEST INSTRUCTIONS")
    print("="*50)
    print("1. The screen will load and say a farewell to 'Alice'.")
    print("2. It will wait 20 seconds.")
    print("3. After 20 seconds, the hint text should appear, and a reminder voice prompt should play.")
    print("4. Press 'B' on your keyboard at any time to simulate the 'BYE' command.")
    print("="*50 + "\n")
    
    sys.exit(app.exec())
