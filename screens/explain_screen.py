import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "explainUI.ui")

window = None
input_enabled = False
explain_data = {}
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
        
    speech_start = explain_data.get("speech_start", "Let's review this concept together.")
    window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
    print(f"🤖 ROBOT SPEAKS: \"{speech_start}\"")
    voice_manager.speak(speech_start, f"explain_start_{task_data.get('task_id', 'id')}")
    
    words_count = len(speech_start.split())
    delay_ms = max(2000, int((words_count / 1.8) * 1000))
    QTimer.singleShot(delay_ms, play_second_speech)

def play_second_speech():
    global explain_data
    speech_end = explain_data.get("speech_end", "Take your time absorbing this. Press Enter when you are ready to continue.")
    
    if speech_end:
        window.robot_text_label.setText(f"🤖 \"{speech_end}\"")
        print(f"🤖 ROBOT SPEAKS: \"{speech_end}\"")
        voice_manager.speak(speech_end, f"explain_end_{explain_data.get('task_id', 'id')}")
        words_count = len(speech_end.split())
        delay_ms = max(2000, int((words_count / 1.8) * 1000))
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
        
        # 2. Rip into Evaluation Sequence natively
        print("[Explain Screen] Transitioning back to Evaluate (Level 3)...")
        from core.flow_controller import flow_controller
        flow_controller.cascade_index = 4
        state_manager.current_stage = "evaluate_L3"
        state_manager.set_affordance_level(3)
        try:
            from core.navigator import navigator
            navigator.navigate_to("evaluate")
        except Exception as e:
            print(f"Warning: Could not transition back to evaluate screen. {e}")
