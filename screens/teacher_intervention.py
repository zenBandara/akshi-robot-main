import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "teacherInterventionUI.ui")

window = None
input_enabled = False

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
    print("[Teacher Intervention Screen] Becoming active...")
    state_manager.set_current_screen("teacher_intervention")
    
    global input_enabled
    input_enabled = False
    
    # 1. Populate Target Adult Warning Message
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    
    message = f"Dear teacher, {student_name} could use a little extra help with this one! 😊"
    window.message_label.setText(message)
    
    # 2. Robotic Reassurance Audio Routine
    # Step 51: Teacher Intervention — Robot Speech
    speech_text = "Let's ask teacher for some help! Don't worry, you did great trying!"
    window.robot_text_label.setText(f"🤖 \"{speech_text}\"")
    
    print(f"🤖 ROBOT SPEAKS [CHEERFUL ENCOURAGING TONE]: \"{speech_text}\"")
    
    # Calculate audio wait sequence (assume steady ~2.5 WPS to keep things calm but brisk)
    words_count = len(speech_text.split())
    delay_ms = max(2000, int((words_count / 2.5) * 1000))
    QTimer.singleShot(delay_ms, enable_input)
    
def enable_input():
    global input_enabled
    input_enabled = True
    print("[Teacher Intervention] Robot finished speaking. Waiting for Teacher Override (Key C).")
    # TODO Step 52: Bind 'C' override via keyboard_manager

def handle_key_press(action):
    pass
