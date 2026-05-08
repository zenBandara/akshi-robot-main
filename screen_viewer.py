#!/usr/bin/env python3
import sys
import os
import json

# Boot PySide6 BEFORE any screen imports
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import QObject, QEvent, Qt

app = QApplication(sys.argv)

# Now safe to import screens
from core.state_manager import state_manager
from core.navigator import navigator
from core.keyboard_manager import keyboard_manager

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TASK_JSON = os.path.join(PROJECT_ROOT, "Tasks", "task_jsons", "t_1.json")

def load_dummy_task():
    try:
        with open(TASK_JSON, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load task: {e}")
        return {}

def setup_state():
    """Pre-populate state_manager with dummy data."""
    state_manager.set_current_student("Dummy Student")
    state_manager.set_current_task(load_dummy_task())
    state_manager.set_affordance_level(1)
    state_manager.set_student_queue(["Student 2", "Student 3"])
    state_manager.current_path = []
    state_manager.set_current_session("demo-session-viewer")

def build_app():
    """Create the main window and stack."""
    main_window = QMainWindow()
    main_window.setWindowTitle("🖥️ Akshi Screen Viewer")
    main_window.setFixedSize(1280, 720)
    main_window.setFocusPolicy(Qt.StrongFocus)

    stack = QStackedWidget()
    stack.setFocusPolicy(Qt.StrongFocus)
    main_window.setCentralWidget(stack)
    navigator.set_stack(stack)
    
    # Global key listener just like main.py so keyboard handlers work normally
    class GlobalKeyListener(QObject):
        def eventFilter(self, obj, event):
            if event.type() == QEvent.Type.KeyPress or event.type() == QEvent.KeyPress:
                keyboard_manager.handle_key_press(event)
                return False
            return super().eventFilter(obj, event)

    key_listener = GlobalKeyListener()
    app.installEventFilter(key_listener)
    
    return main_window, key_listener

SCREENS_MAP = {
    1: ("calibration", "Face Calibration Screen"),
    2: ("engage", "Engage Screen (Level 2)"),
    3: ("explore", "Explore Screen (Level 3)"),
    4: ("explain", "Explain Screen (Level 3)"),
    5: ("elaborate", "Elaborate Screen (Level 3)"),
    6: ("evaluate", "Evaluate Screen (Evaluation)"),
    7: ("kinestatic", "Kinesthetic Learning Loop"),
    8: ("teacher_intervention", "Teacher Intervention Screen"),
    9: ("break", "Rabbit Jump Break Screen"),
    10: ("celebration", "Celebration Screen"),
    11: ("task_intro", "Task Introduction Screen"),
    12: ("greeting", "Greeting Screen"),
    13: ("student_call", "Student Call Screen"),
    14: ("teacher_select", "Teacher Selection Screen"),
    15: ("session_complete", "Session Complete Screen"),
}

def print_cheat_sheet():
    print("\n" + "="*50)
    print("🎬 AKSHI SCREEN VIEWER CHEAT SHEET")
    print("="*50)
    print("Usage: python screen_viewer.py <screen_number>\n")
    for key, (screen_id, desc) in sorted(SCREENS_MAP.items()):
        print(f"  {key:2d} — {desc}")
    print("="*50 + "\n")

def register_screens():
    """Import and register all screens."""
    screen_map = {}
    from screens import evaluate_screen, celebration_screen, calibration_screen, kinestatic, break_screen, teacher_intervention, greeting_screen, engage_screen, explore_screen, explain_screen, elaborate_screen, student_call_screen, session_complete_screen, task_intro_screen, teacher_select
    
    screen_map["evaluate"] = evaluate_screen.get_ui()
    screen_map["celebration"] = celebration_screen.get_ui()
    screen_map["calibration"] = calibration_screen.get_ui()
    screen_map["kinestatic"] = kinestatic.get_ui()
    screen_map["break"] = break_screen.get_ui()
    screen_map["teacher_intervention"] = teacher_intervention.get_ui()
    screen_map["greeting"] = greeting_screen.get_ui()
    screen_map["engage"] = engage_screen.get_ui()
    screen_map["explore"] = explore_screen.get_ui()
    screen_map["explain"] = explain_screen.get_ui()
    screen_map["elaborate"] = elaborate_screen.get_ui()
    screen_map["student_call"] = student_call_screen.get_ui()
    screen_map["session_complete"] = session_complete_screen.get_ui()
    screen_map["task_intro"] = task_intro_screen.get_ui()
    screen_map["teacher_select"] = teacher_select.get_ui()
    
    for name, widget in screen_map.items():
        if widget:
            navigator.register_screen(name, widget)

def main():
    if len(sys.argv) < 2:
        print_cheat_sheet()
        sys.exit(0)
        
    try:
        screen_num = int(sys.argv[1])
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        print_cheat_sheet()
        sys.exit(1)
        
    if screen_num not in SCREENS_MAP:
        print(f"❌ Screen number {screen_num} not found.")
        print_cheat_sheet()
        sys.exit(1)
        
    target_screen_id, desc = SCREENS_MAP[screen_num]

    setup_state()
    main_window, listener = build_app()
    register_screens()
    
    print(f"\n🚀 Launching: {desc} ({target_screen_id})")
    
    main_window.show()
    navigator.navigate_to(target_screen_id)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
