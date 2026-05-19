import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QPropertyAnimation, Qt, QUrl
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QPixmap
from core.keyboard_manager import keyboard_manager
from core.state_manager import state_manager
from core.navigator import navigator
from components.robot_eyes import get_robot_eyes

window = None
pulse_anim = None
fade_effect = None
video_label = None
frame_timer = None
current_frames = []
current_frame_idx = 0

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    ui_path = os.path.join(project_root, "ui", "idleUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    # ── TOUCHSCREEN QUIT BUTTON ──
    # Create a large, translucent button in the bottom-left for system exit
    quit_btn = QPushButton("✖ Quit", window)
    quit_btn.setFixedSize(120, 60)
    quit_btn.move(20, 640) # Bottom-left on 1280x720 canvas
    quit_btn.setStyleSheet("""
        QPushButton {
            background-color: rgba(255, 0, 0, 50);
            color: white;
            border-radius: 30px;
            font-size: 18px;
            font-weight: bold;
            border: 2px solid rgba(255, 255, 255, 80);
        }
        QPushButton:pressed {
            background-color: rgba(255, 0, 0, 150);
        }
    """)
    quit_btn.clicked.connect(lambda: QApplication.instance().quit())

    setup_animations()
    
    # Standardize lifecycle hooks for Navigator
    def on_show():
        print("[Idle Screen] Becoming active with native Video Engine...")
        keyboard_manager.register_handler(handle_key_press)
        state_manager.set_current_screen("idle")
        get_robot_eyes().set_expression("default")
        
        # Deploy image sequence pipeline gracefully
        if frame_timer is None:
            setup_video()
        else:
            frame_timer.start(66)

    window.on_show = on_show
    return window

def setup_animations():
    global window, pulse_anim, fade_effect
    
    # 1. Slow glowing pulse for the hint label natively
    fade_effect = QGraphicsOpacityEffect(window.hint_label)
    window.hint_label.setGraphicsEffect(fade_effect)
    
    pulse_anim = QPropertyAnimation(fade_effect, b"opacity")
    pulse_anim.setDuration(2500)
    pulse_anim.setStartValue(0.2)
    pulse_anim.setKeyValueAt(0.5, 1.0)
    pulse_anim.setEndValue(0.2)
    pulse_anim.setLoopCount(-1) # Infinite loop
    pulse_anim.start()

def setup_video():
    global window, video_label, frame_timer, current_frames, current_frame_idx
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    video_dir = os.path.join(project_root, "assets", "video", "idle")
    
    if video_label is None:
        video_label = QLabel()
        video_label.setAlignment(Qt.AlignCenter)
        video_label.setScaledContents(True)
    
    # Dynamically mount directly into the centralized Web Container GUI layout frame
    layout = QVBoxLayout(window.web_container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(video_label)
    
    if os.path.isdir(video_dir):
        frames = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith('.jpg')]
        frames.sort()
        current_frames = frames
        current_frame_idx = 0
    else:
        print(f"[Idle Screen] Idle image sequence not found: {video_dir}")
        return
        
    if frame_timer is None:
        frame_timer = QTimer()
        frame_timer.timeout.connect(update_frame)
    frame_timer.start(66) # ~15 FPS

def update_frame():
    global current_frames, current_frame_idx, video_label
    if current_frames and video_label:
        pixmap = QPixmap(current_frames[current_frame_idx])
        video_label.setPixmap(pixmap)
        current_frame_idx = (current_frame_idx + 1) % len(current_frames)

def handle_key_press(mapped_action):
    global frame_timer
    if mapped_action == "WAKE":
        print("[Idle Screen] WAKE command triggered! Starting new session & fetching data...")
        
        # Log telemetry for research
        try:
            from core.telemetry_logger import telemetry_logger
            telemetry_logger.log_event("USER_INPUT", detail="Robot WAKE command triggered")
        except Exception:
            pass

        get_robot_eyes().set_expression("surprised")
        selected_teacher = state_manager.get_selected_teacher()
        if selected_teacher:
            from core import firebase
            import random
            import core.task_loader as task_loader
            import core.database as database
            
            # Start new telemetry session
            current_session = database.start_session(selected_teacher)
            state_manager.set_current_session(current_session)
            print(f"[Idle Screen] New session started: {current_session}")
            
            # Fetch latest students
            students = firebase.get_students(selected_teacher)
            state_manager.set_student_list(students)
            student_queue = students.copy()
            random.shuffle(student_queue)
            state_manager.set_student_queue(student_queue)
            state_manager.has_shown_task_intro = False
            
            # Fetch single task
            lesson_id = firebase.get_current_lesson(selected_teacher)
            all_tasks = task_loader.get_loaded_tasks()
            lesson_data = next((t for t in all_tasks if t.get("task_id") == lesson_id), None)
            if not lesson_data:
                lesson_data = next((t for t in all_tasks if t.get("task_id") == "t_2"), None)
            state_manager.set_current_task(lesson_data)
            print(f"[Idle Screen] Fetched task: {lesson_data.get('task_id') if lesson_data else 'None'}")
            
        if frame_timer is not None:
            frame_timer.stop()
        navigator.navigate_to("greeting")
