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
    
    # Needs to run async or handle slight UI freezup if network is slow, 
    # but for simplicity we rely on firebase_admin caching
    teachers = firebase.get_teachers()
    
    # Flush existing Layout Cards physically from PySide6 memory hooks
    while window.cards_container.layout().count():
        child = window.cards_container.layout().takeAt(0)
        if child.widget(): child.widget().deleteLater()
    
    from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout
    from PySide6.QtCore import Qt

    if not teachers:
        error_label = QLabel("No teachers found.\nPlease check connection.")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("font-size: 24px; color: #D32F2F;")
        window.cards_container.layout().addWidget(error_label)
        return

    teacher_map.clear()
    
    for i, teacher_id in enumerate(teachers):
        if i >= 26: break # Only map up to Z
        key_char = chr(ord('A') + i)
        
        # We must map to the internal action name if the key is reserved globally (e.g. B -> BREAK)
        key_code = Qt.Key_A + i
        mapped_action = keyboard_manager.key_mapping.get(key_code, key_char)
        teacher_map[mapped_action] = teacher_id
        
        # Build highly-professional CSS Teacher Card component natively
        card = QFrame()
        card.setFixedHeight(75)
        card.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 0, 20, 0)
        
        # Synthesize vivid blue Typography Badge constraint
        badge = QLabel(f"{key_char}")
        badge.setFixedSize(45, 45)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet("""
            QLabel {
                background-color: #1976D2;
                color: #FFFFFF;
                font-size: 22px;
                font-weight: bold;
                border-radius: 22px;
                border: none;
            }
        """)
        
        # Inject raw Email typography natively 
        email_label = QLabel(teacher_id)
        email_label.setStyleSheet("""
            QLabel {
                color: #334155;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        
        card_layout.addWidget(badge)
        card_layout.addSpacing(20)
        card_layout.addWidget(email_label)
        card_layout.addStretch()
        
        window.cards_container.layout().addWidget(card)

def handle_key_press(mapped_action):
    # E.g. mapped_action == "A"
    if mapped_action in teacher_map:
        keyboard_manager.unregister_handler()  # Prevent duplicate key events from re-triggering the flow
        selected_teacher = teacher_map[mapped_action]
        print(f"Teacher selected: {selected_teacher}")
        
        state_manager.set_selected_teacher(selected_teacher)
        window.title_label.setText("Authenticating Teacher...")
        
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
        window.title_label.setText(f"Loading session for {selected_teacher}...")
        
        # Strip all dynamically generated teacher cards visibly immediately indicating process consumption
        while window.cards_container.layout().count():
            child = window.cards_container.layout().takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        import core.session_logic as session_logic
        session_logic.next_student()
