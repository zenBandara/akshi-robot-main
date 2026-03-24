import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QPropertyAnimation, QTimer, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator
from core.voice_manager import VoiceManager

window = None
fade_anim = None
fade_effect = None
voice_manager = VoiceManager()

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    ui_path = os.path.join(project_root, "ui", "studentCallUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    setup_animations()

    def on_show():
        print("[Student Call Screen] Becoming active...")
        state_manager.set_current_screen("student_call")
        keyboard_manager.register_handler(handle_key_press)
        
        student_name = state_manager.get_current_student()
        display_name = student_name if student_name else "Buddy"
        
        # Unconditionally extract the active hierarchical phase payload directly from state metadata constraints
        current_task = state_manager.get_current_task()
        task_name = current_task.get("task_name", "a fun new activity") if current_task else "a fun new activity"
        
        window.student_name_label.setText(f"{display_name}! 🎉")
        
        # Mathematically construct the highly-professional, highly-conversational dynamically cached TTS execution loop
        student_list = state_manager.get_student_list()
        student_queue = state_manager.get_student_queue()
        # It's the first chronological student if exactly one student has been popped from the queue
        is_first_student = (len(student_queue) == len(student_list) - 1) if student_list else True
        
        if is_first_student:
            intro_msg = f"Hello my wonderful friends! Today, we are going to learn all about {task_name}! It is going to be so much fun. {display_name}, can you please come on up? It is your turn to shine!"
        else:
            intro_msg = f"Wow, you guys are doing great! {display_name}, can you please come on up? It is your turn to shine!"
        
        print(f"[Robot Speaks]: {intro_msg}")
        duration_ms = voice_manager.speak(intro_msg, f"call_{display_name}_{task_name.replace(' ', '_').lower()}")
            
        if fade_anim:
            fade_effect.setOpacity(0.0)
            fade_anim.start()

    window.on_show = on_show
    return window

def setup_animations():
    global window, fade_anim, fade_effect
    
    fade_effect = QGraphicsOpacityEffect(window.student_name_label)
    window.student_name_label.setGraphicsEffect(fade_effect)
    
    fade_anim = QPropertyAnimation(fade_effect, b"opacity")
    fade_anim.setDuration(1200)
    fade_anim.setStartValue(0.0)
    fade_anim.setEndValue(1.0)
    fade_anim.setEasingCurve(QEasingCurve.OutCubic)

def handle_key_press(mapped_action):
    if mapped_action == "ENTER" or mapped_action == "CONTINUE":
        keyboard_manager.unregister_handler()
        voice_manager.stop()
        print("Student cleanly interrupted intro! Transitioning to Evaluate Screen natively...")
        state_manager.set_five_e_stage("evaluate")
        state_manager.set_affordance_level(1)
        
        # Navigate strictly to the new Phase 3 Evaluate Engine
        navigator.navigate_to("evaluate")
