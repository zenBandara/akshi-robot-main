#!/usr/bin/env python3
"""
🚀 Level 3 Evaluation Preview Tool
==================================
Standalone tool to jump directly into the Gamified Level 3 Evaluation
using Task 4 data.

Usage:
    python test_level3_eval.py
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

# Mocking flow_controller and other parts that might depend on Firebase
import core.state_manager as sm
import core.navigator as nav

def setup_mock_state():
    # 1. Load Task 4 data
    task_path = os.path.join("Tasks", "task_jsons", "t_4.json")
    try:
        with open(task_path, "r") as f:
            task_data = json.load(f)
            sm.state_manager.set_current_task(task_data)
            print(f"✅ Loaded Task 4: {task_data.get('task_name')}")
    except Exception as e:
        print(f"❌ Error loading task data: {e}")
        sys.exit(1)

    # 2. Set student and level
    sm.state_manager.set_current_student("Superstar")
    sm.state_manager.set_affordance_level(3)
    print("✅ Set Level: 3")
    print("✅ Set Student: Superstar")

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Jinglu Gamified L3 Preview")
        self.setFixedSize(1280, 720)

        # Create the Stacked Widget (The "Brain")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Initialize the navigator with our stack
        nav.navigator.set_stack(self.stack)

        # Register and show the evaluation screen
        from screens import evaluate_screen
        eval_widget = evaluate_screen.get_ui()
        nav.navigator.register_screen("evaluate", eval_widget)
        
        # Jump directly to it
        nav.navigator.navigate_to("evaluate")

    def keyPressEvent(self, event):
        # Pass key events to keyboard_manager
        from core.keyboard_manager import keyboard_manager
        keyboard_manager.handle_key_press(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Initialize mock state BEFORE UI
    setup_mock_state()
    
    # Create and show window
    window = TestWindow()
    window.show()
    
    print("\n🎮 CONTROLS:")
    print("  [1] → Answer YES")
    print("  [2] → Answer NO")
    print("  [Esc] → Quit")
    
    sys.exit(app.exec())
