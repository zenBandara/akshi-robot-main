import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "explainUI.ui")

window = None
input_enabled = False
explain_data = {}

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
    print("[Explain Screen] Becoming active...")
    state_manager.set_current_screen("explain")
    
    task_data = state_manager.get_current_task()
    if not task_data or "explain" not in task_data:
        print("Error: No valid explain task found in state_manager.")
        window.title_label.setText("Error: Task not loaded.")
        return
        
    explain_data = task_data.get("explain", {})
    
    # 1. Populate Title
    window.title_label.setText(explain_data.get("task_title", "Let's Understand This Better!"))
    
    # 2. Populate Explanation Text
    desc_text = explain_data.get("task_description", "")
    if not desc_text:
        # Fallback to the speech_start script if the JSON didn't include a physical description
        desc_text = explain_data.get("speech_start", "Here is a detailed explanation.")
    window.explanation_label.setText(desc_text)
    
    # 3. Populate Media Payload
    media_url = explain_data.get("video_url", "")
    if media_url:
        abs_media_path = os.path.join(project_root, media_url)
        if os.path.exists(abs_media_path):
            pixmap = QPixmap(abs_media_path)
            window.media_label.setPixmap(pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            window.media_label.setText("🖼️\n[Media File Missing]")
    else:
        window.media_label.setText("🖼️\n[No Media Provided]")
        
    # 4. Multi-Stage Robot Speech Loop
    global input_enabled, explain_data
    input_enabled = False
    explain_data = task_data.get("explain", {})
    
    speech_start = explain_data.get("speech_start", "Let's review this concept together.")
    window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
    print(f"🤖 ROBOT SPEAKS: \"{speech_start}\"")
    
    words_count = len(speech_start.split())
    delay_ms = max(2000, int((words_count / 2.5) * 1000))
    QTimer.singleShot(delay_ms, play_second_speech)

def play_second_speech():
    global explain_data
    speech_end = explain_data.get("speech_end", "Take your time absorbing this. Press Enter when you are ready to continue.")
    
    if speech_end:
        window.robot_text_label.setText(f"🤖 \"{speech_end}\"")
        print(f"🤖 ROBOT SPEAKS: \"{speech_end}\"")
        words_count = len(speech_end.split())
        delay_ms = max(2000, int((words_count / 2.5) * 1000))
        QTimer.singleShot(delay_ms, enable_input)
    else:
        enable_input()

def enable_input():
    global input_enabled
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)
    window.robot_text_label.setText("🤖 Waiting for input...")
    print("[Explain Screen] Robot fully finished speaking. Keyboard hardware inputs physically enabled.")

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action == "ENTER": # Hardware mapping for Return/Enter
        input_enabled = False
        print("[Explain Screen] Student pressed ENTER. Logging failure and advancing...")
        
        # 1. Log the Failure Interaction natively
        task_data = state_manager.get_current_task()
        task_id = task_data.get("task_id", "unknown") if task_data else "unknown"
        student_id = state_manager.get_current_student() or "unknown"
        
        log_data = {
            "student_id": student_id,
            "task_id": task_id,
            "result": "incorrect",
            "affordance_level_reached": state_manager.get_affordance_level(),
            "path_taken": ["evaluate_L1", "elaborate", "evaluate_L2", "explain"]
        }
        
        if not hasattr(state_manager, 'session_logs'):
            state_manager.session_logs = []
        state_manager.session_logs.append(log_data)
        
        try:
            from core import firebase
            firebase.log_event(log_data)
        except ImportError:
            pass
            
        print(f"[Explain Screen] LOGGED FAILURE: {log_data}")
        
        # 2. Rip next student & reset system globals
        student_queue = state_manager.get_student_queue()
        parent_stack = window.parentWidget()
        
        if student_queue:
            next_stu = student_queue.pop(0)
            state_manager.set_current_student(next_stu)
            state_manager.set_student_queue(student_queue)
            
            # Wipe affordance state gracefully for the new human
            if hasattr(state_manager, 'current_path'):
                state_manager.current_path = []
            state_manager.set_affordance_level(1)
            
            print(f"[Explain Screen] Advancing to next student: {next_stu}...")
            try:
                from screens import greeting_screen
                if parent_stack:
                    greeting_ui = greeting_screen.get_ui()
                    parent_stack.addWidget(greeting_ui)
                    parent_stack.setCurrentWidget(greeting_ui)
            except ImportError:
                print("Warning: Could not load greeting_screen.")
        else:
            print("[Explain Screen] Queue empty! Moving natively to Session Complete.")
            try:
                from screens import session_complete
                if parent_stack:
                    session_complete_ui = session_complete.get_ui()
                    parent_stack.addWidget(session_complete_ui)
                    parent_stack.setCurrentWidget(session_complete_ui)
            except ImportError:
                print("Warning: Could not load session_complete.")
