#!/usr/bin/env python3
"""
🧪 Task Intro Screen Tester
===========================
Standalone tool to verify the Task Introduction screen and its 
data loading logic.

Usage:
    python test_task_intro.py
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

import core.state_manager as sm
import core.navigator as nav

def setup_mock_state():
    # Load Task 4
    task_path = os.path.join("Tasks", "task_jsons", "t_4.json")
    try:
        with open(task_path, "r") as f:
            task_data = json.load(f)
            sm.state_manager.set_current_task(task_data)
            print(f"✅ Mocked State: Current Task = {task_data.get('task_name')}")
    except Exception as e:
        print(f"❌ Error loading task data: {e}")
        sys.exit(1)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 Task Intro Preview")
        self.setFixedSize(1280, 720)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        nav.navigator.set_stack(self.stack)

        from screens import task_intro_screen
        intro_widget = task_intro_screen.get_ui()
        nav.navigator.register_screen("task_intro", intro_widget)
        
        nav.navigator.navigate_to("task_intro")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    setup_mock_state()
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())
