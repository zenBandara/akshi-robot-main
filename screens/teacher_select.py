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

    def on_show():
        print("[Teacher Select Screen] Becoming active...")
        state_manager.set_current_screen("teacher_select")
        keyboard_manager.register_handler(handle_key_press)
        load_teachers()

    window.on_show = on_show
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
    
    from PySide6.QtCore import Qt
    
    for i, teacher_id in enumerate(teachers):
        if i >= 26: break # Only map up to Z
        key_char = chr(ord('A') + i)
        
        # We must map to the internal action name if the key is reserved globally (e.g. B -> BREAK)
        key_code = Qt.Key_A + i
        mapped_action = keyboard_manager.key_mapping.get(key_code, key_char)
        
        teacher_map[mapped_action] = teacher_id
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
        
        import random
        import core.task_loader as task_loader
        
        # Fetch students and lesson config to state manager
        students = firebase.get_students(selected_teacher)
        lesson_id = firebase.get_current_lesson(selected_teacher)
        
        # Resolve physical JSON dictionary payload instead of raw string IDs
        all_tasks = task_loader.get_loaded_tasks()
        lesson_data = next((t for t in all_tasks if t.get("task_id") == lesson_id), None)
        
        if not lesson_data:
            print(f"Warning: Lesson {lesson_id} not physically found on disk. Falling back to random structure.")
            lesson_data = task_loader.pick_random_task()
            
        state_manager.set_student_list(students)
        state_manager.set_current_task(lesson_data)
        
        # Create a shuffled queue
        student_queue = students.copy()
        random.shuffle(student_queue)
        state_manager.set_student_queue(student_queue)
        
        print("Teacher selected. Proceeding to select first student...")
        window.teacher_list_label.setText(f"Great! {selected_teacher} Selected!\n\nPicking a student...")
        
        import core.session_logic as session_logic
        session_logic.next_student()
