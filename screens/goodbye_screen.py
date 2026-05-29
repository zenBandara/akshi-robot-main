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
prompt_timer = None

def get_ui():
    global window, prompt_timer
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
    
    # Initialize our 20-second loop timer
    prompt_timer = QTimer()
    prompt_timer.setInterval(20000) # 20 seconds
    prompt_timer.timeout.connect(prompt_for_bye)

    def on_show():
        print("[Goodbye Screen] Becoming active...")
        state_manager.set_current_screen("goodbye")
        
        # Ensure timer is stopped when we start
        prompt_timer.stop()
        
        # Black frames during the goodbye speech
        try:
            set_frame_streaming(False, reason="goodbye_screen")
        except Exception as e:
            print("[Goodbye Screen] Error pausing frames:", e)
            
        voice_manager.stop()  
        keyboard_manager.unregister_handler()
        
        student_name = state_manager.get_current_student()
        display_name = str(student_name).capitalize() if student_name else "Buddy"
        
        window.student_name_label.setText(f"Bye {display_name}! 👋")
        # Hide the hint label initially
        window.hint_label.setText("")
        
        window.update()
        QApplication.processEvents()

        get_robot_eyes().set_expression("encouraging")
        
        # Initial speech doesn't ask for bye yet
        intro_template = "You did amazing today, {name}! Bye!"
        print(f"[Robot Speaks]: {intro_template.replace('{name}', display_name)}")
        duration_ms = voice_manager.speak_with_name(intro_template, display_name, f"goodbye_{display_name}")
            
        if hasattr(window, "student_name_label"):
            window.student_name_label.setGraphicsEffect(None)
            
        # Enable input and start the 20-second reminder timer after the initial speech finishes
        def on_speech_done():
            keyboard_manager.register_handler(handle_key_press)
            prompt_timer.start()
            
        QTimer.singleShot(duration_ms + 200, on_speech_done)

    window.on_show = on_show
    return window

def prompt_for_bye():
    """Triggered every 20 seconds if the student hasn't said BYE yet."""
    global window
    if not window: return
    
    window.hint_label.setText("Say 'Bye' to finish your turn! 🌟")
    window.update()
    QApplication.processEvents()
    
    msg = "Alright superstar, say 'bye' so your friends can have a turn!"
    print(f"[Goodbye Screen Reminder]: {msg}")
    voice_manager.speak(msg, "goodbye_reminder")

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
    global prompt_timer
    if mapped_action == "BYE":
        keyboard_manager.unregister_handler()
        voice_manager.stop()
        if prompt_timer:
            prompt_timer.stop()
            
        get_robot_eyes().set_expression("default")
        print("[Goodbye Screen] Student said BYE. Moving to next student...")
        import core.session_logic as session_logic
        session_logic.next_student()
