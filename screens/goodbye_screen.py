import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QPropertyAnimation, QTimer, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect, QApplication
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes
from core.stream_control import set_frame_streaming

window = None
fade_anim = None
fade_effect = None
voice_manager = VoiceManager()

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    # Reuse studentCallUI for a consistent layout
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
        print("[Goodbye Screen] Becoming active...")
        state_manager.set_current_screen("goodbye")
        
        # Black frames during the goodbye speech
        try:
            set_frame_streaming(False, reason="goodbye_screen")
        except Exception as e:
            print("[Goodbye Screen] Error pausing frames:", e)
            
        voice_manager.stop()  
        keyboard_manager.unregister_handler()
        
        student_name = state_manager.get_current_student()
        display_name = str(student_name).capitalize() if student_name else "Buddy"
        
        window.student_name_label.setText(f"Goodbye {display_name}! 👋")
        window.hint_label.setText("Say 'Yes' to finish your turn! 🌟")
        
        window.update()
        QApplication.processEvents()

        get_robot_eyes().set_expression("encouraging")
        
        intro_template = "You did amazing today, {name}! Please say 'Yes' so your friend can have a turn!"
        print(f"[Robot Speaks]: {intro_template.replace('{name}', display_name)}")
        duration_ms = voice_manager.speak_with_name(intro_template, display_name, f"goodbye_{display_name}")
            
        if hasattr(window, "student_name_label"):
            window.student_name_label.setGraphicsEffect(None)
            
        # Enable input after speech finishes
        QTimer.singleShot(duration_ms + 200, lambda: keyboard_manager.register_handler(handle_key_press))

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
    if mapped_action in ["ENTER", "YES"]:
        keyboard_manager.unregister_handler()
        voice_manager.stop()
        get_robot_eyes().set_expression("default")
        print("[Goodbye Screen] Student said YES. Moving to next student...")
        import core.session_logic as session_logic
        session_logic.next_student()
