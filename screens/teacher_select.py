import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator
from core import firebase

window = None
teacher_map = {}

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    ui_path = os.path.join(project_root, "ui", "teacherSelectUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    def handle_show_event(event):
        state_manager.set_current_screen("teacher_select")
        keyboard_manager.register_handler(handle_key_press)
        load_teachers()

    window.showEvent = handle_show_event
    return window

def load_teachers():
    global teacher_map
    window.teacher_list_label.setText("Fetching teachers from Firebase...")
    
    # Needs to run async or handle slight UI freezup if network is slow, 
    # but for simplicity we rely on firebase_admin caching
    teachers = firebase.get_teachers()
    
    if not teachers:
        window.teacher_list_label.setText("No teachers found.\nPlease check connection.")
        return

    teacher_map.clear()
    display_text = ""
    
    for i, teacher_id in enumerate(teachers):
        if i >= 26: break # Only map up to Z
        key_char = chr(ord('A') + i)
        teacher_map[key_char] = teacher_id
        display_text += f"[ {key_char} ] - {teacher_id}\n\n"

    display_text += "\nPress the corresponding letter key!"
    window.teacher_list_label.setText(display_text)

def handle_key_press(mapped_action):
    # E.g. mapped_action == "A"
    if mapped_action in teacher_map:
        selected_teacher = teacher_map[mapped_action]
        print(f"Teacher selected: {selected_teacher}")
        
        state_manager.set_selected_teacher(selected_teacher)
        
        window.teacher_list_label.setText(f"Loading students for {selected_teacher}...")
        
        # Fetch students and save to state manager
        students = firebase.get_students(selected_teacher)
        state_manager.set_student_list(students)
        print(f"Loaded {len(students)} students.")
        
        print("Transitioning to Student Calling Screen...")
        navigator.navigate_to("student_calling")
