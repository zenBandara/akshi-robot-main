import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.state_manager import state_manager
from core.navigator import navigator
from core.voice_manager import VoiceManager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "taskIntroUI.ui")

window = None
voice_manager = VoiceManager()
name_opacity = None
name_anim = None

def get_ui():
    global window
    if window is None:
        loader = QUiLoader()
        file = QFile(ui_path)
        if not file.open(QFile.ReadOnly):
            print("Cannot open UI file:", ui_path)
            return None
        window = loader.load(file)
        file.close()
        
        window.on_show = on_show
        
    return window

def on_show():
    global name_opacity, name_anim
    print("[Task Intro Screen] Becoming active...")
    state_manager.set_current_screen("task_intro")
    
    # Pause frames during task introduction
    try:
        import json
        with open("akshi-the-robot/calibration_command.json", "w") as f:
            json.dump({"type": "pause_frames"}, f)
    except Exception as e:
        print("[Task Intro Screen] Error pausing frames:", e)
    
    # Stop any lingering audio from the previous screen
    voice_manager.stop()
    
    # Get task data
    task_data = state_manager.get_current_task()
    task_name = task_data.get("task_name", "A Fun Activity") if task_data else "A Fun Activity"
    
    # Populate UI
    window.task_name_label.setText(task_name)
    
    # Fade-in animation for the task name
    name_opacity = QGraphicsOpacityEffect(window.task_name_label)
    window.task_name_label.setGraphicsEffect(name_opacity)
    name_opacity.setOpacity(0.0)
    
    name_anim = QPropertyAnimation(name_opacity, b"opacity")
    name_anim.setDuration(1200)
    name_anim.setStartValue(0.0)
    name_anim.setEndValue(1.0)
    name_anim.setEasingCurve(QEasingCurve.OutCubic)
    name_anim.start()
    
    # Robot introduces the task
    intro_speech = f"Hello my wonderful friends! Today, we are going to learn all about {task_name}! It is going to be so much fun. Let's get started!"
    print(f"[Robot Speaks]: {intro_speech}")
    
    duration_ms = 5000
    try:
        duration_ms = voice_manager.speak(intro_speech, f"task_intro_{task_name.replace(' ', '_').lower()}")
    except Exception as e:
        print(f"VoiceManager error: {e}")
    
    # After speech finishes, automatically transition to student call
    QTimer.singleShot(duration_ms, transition_to_student_call)

def transition_to_student_call():
    print("[Task Intro Screen] Transitioning to Student Call...")
    navigator.navigate_to("student_call")
