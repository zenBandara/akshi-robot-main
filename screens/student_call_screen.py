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
        
        # Pause frames during student selection
        try:
            import json
            with open("akshi-the-robot/calibration_command.json", "w") as f:
                json.dump({"type": "pause_frames"}, f)
        except Exception as e:
            print("[Student Call Screen] Error pausing frames:", e)
            
        voice_manager.stop()  # Kill any lingering audio from task_intro or previous screens
        keyboard_manager.register_handler(handle_key_press)
        
        student_name = state_manager.get_current_student()
        display_name = student_name if student_name else "Buddy"
        
        window.student_name_label.setText(f"{display_name}! 🎉")
        window.hint_label.setText("Say 'Okay' when you're ready! 🌟")
        
        # Simple call — the task introduction is handled by the dedicated task_intro_screen
        intro_msg = f"{display_name}, can you please come on up? It is your turn to shine!"
        
        print(f"[Robot Speaks]: {intro_msg}")
        duration_ms = voice_manager.speak(intro_msg, f"call_{display_name}")
            
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
    if mapped_action == "ENTER":
        keyboard_manager.unregister_handler()
        voice_manager.stop()
        print("Student cleanly interrupted intro! Transitioning to Calibration Screen...")
        # Route to calibration for face tracking BEFORE starting the learning flow
        navigator.navigate_to("calibration")

