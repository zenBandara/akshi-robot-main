import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "teacherInterventionUI.ui")

window = None
input_enabled = False
voice_manager = VoiceManager()

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
    delay_ms = voice_manager.speak(speech_text, f"teacher_intervention_{student_name}")
    
    print(f"Enabling keyboard input immediately to allow for speech interruption.")
    enable_input()
    
def enable_input():
    global input_enabled
    input_enabled = True
    print("[Teacher Intervention] Robot finished speaking. Waiting for Teacher Override (Key C).")
    # Step 52: Bind 'C' override via keyboard_manager
    keyboard_manager.register_handler(handle_key_press)

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action == "CONTINUE":
        input_enabled = False
        voice_manager.stop()
        print("[Teacher Intervention] Teacher pressed CONTINUE. Logging complete cascade and resetting.")
        
        # Log Result (Complete Cascade Failure -> Teacher Assisted)
        task_data = state_manager.get_current_task()
        task_id = task_data.get("task_id", "unknown") if task_data else "unknown"
        student_id = state_manager.get_current_student() or "unknown"
        
        # Hard-code the absolute deepest fallback sequence manually
        state_manager.current_path = [
            "evaluate_L1", "elaborate", "evaluate_L2", "explain", 
            "evaluate_L3", "explore", "evaluate_L3", "engage", 
            "evaluate_L3", "teacher_intervention"
        ]
        
        log_data = {
            "student_id": student_id,
            "task_id": task_id,
            "result": "teacher_assisted",
            "affordance_level_reached": getattr(state_manager, "affordance_level", 3),
            "path_taken": state_manager.current_path
        }
        
        if not hasattr(state_manager, 'session_logs'):
            state_manager.session_logs = []
        state_manager.session_logs.append(log_data)
        
        try:
            from core import firebase
            firebase.log_event(log_data)
        except ImportError: pass
            
        print(f"[Teacher Intervention] LOGGED FINAL TASK RESULT: {log_data}")
        
        # Advance Queue Natively
        # Advance Queue Natively
        student_queue = state_manager.get_student_queue()
        
        if student_queue:
            next_stu = student_queue.pop(0)
            state_manager.set_current_student(next_stu)
            state_manager.set_student_queue(student_queue)
            
            # Wipe affordance tracking state completely for the next child
            state_manager.current_path = []
            state_manager.set_affordance_level(1)
            
            try:
                from core.navigator import navigator
                navigator.navigate_to("student_call")
            except Exception as e:
                print(f"Warning: Could not transition back to student_call screen. {e}")
        else:
            try:
                from core.navigator import navigator
                navigator.navigate_to("session_complete")
            except Exception as e:
                print(f"Warning: Could not transition back to session_complete screen. {e}")
