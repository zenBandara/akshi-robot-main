import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "exploreUI.ui")

window = None
input_enabled = False
explore_data = {}

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
    print("[Explore Screen] Becoming active...")
    state_manager.set_current_screen("explore")
    
    task_data = state_manager.get_current_task()
    if not task_data or "explore" not in task_data:
        print("Error: No valid explore task found in state_manager.")
        window.title_label.setText("Error: Task not loaded.")
        return
        
    global input_enabled, explore_data
    input_enabled = False
    explore_data = task_data.get("explore", {})
    
    # 1. Populate Title
    window.title_label.setText(explore_data.get("task_title", "Let's Explore!"))
    
    # 2. Populate Kinesthetic Activity Text
    desc_text = explore_data.get("task_description", "")
    if not desc_text:
        desc_text = explore_data.get("speech_start", "Move your body to explore this concept!")
    window.activity_label.setText(desc_text)
    
    # 3. Populate Media/Video Loop
    media_url = explore_data.get("video_url", "")
    if media_url:
        abs_media_path = os.path.join(project_root, media_url)
        if os.path.exists(abs_media_path):
            pixmap = QPixmap(abs_media_path)
            window.media_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            window.media_label.setText("🖐️\n[Media File Missing]")
    else:
        window.media_label.setText("🖐️\n[No Visual Prompt Provided]")
        
    # 4. Multi-Stage Kinesthetic Robot Speech Loop
    global input_enabled, explore_data
    input_enabled = False
    explore_data = task_data.get("explore", {})
    
    speech_start = explore_data.get("speech_start", "Let's try a physical activity!")
    # Step 44: Physically Encourage Kinesthetic Output
    speech_start = f"Stand up! {speech_start}"
    
    window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
    print(f"🤖 ROBOT SPEAKS: \"{speech_start}\"")
    
    words_count = len(speech_start.split())
    delay_ms = max(2000, int((words_count / 2.5) * 1000))
    QTimer.singleShot(delay_ms, play_second_speech)

def play_second_speech():
    global explore_data
    speech_end = explore_data.get("speech_end", "Press Enter when you're done exploring!")
    
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
    window.robot_text_label.setText("🤖 Waiting for you to finish exploring...")
    print("[Explore Screen] Robot fully finished speaking. Keyboard hardware inputs physically enabled.")
    # Step 45: Bind keyboard handler
    keyboard_manager.register_handler(handle_key_press)

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action == "ENTER":
        input_enabled = False
        print("[Explore Screen] Student pressed ENTER. Ending Exploration and moving to next student.")
        
        # Log Result (Deep Failure -> Explored)
        task_data = state_manager.get_current_task()
        task_id = task_data.get("task_id", "unknown") if task_data else "unknown"
        student_id = state_manager.get_current_student() or "unknown"
        
        # Hard-code the absolute deepest fallback sequence manually
        state_manager.current_path = ["evaluate_L1", "elaborate", "evaluate_L2", "explain", "evaluate_L3", "explore"]
        
        log_data = {
            "student_id": student_id,
            "task_id": task_id,
            "result": "incorrect",
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
            
        print(f"[Explore Screen] LOGGED FINAL TASK RESULT: {log_data}")
        
        # Advance Queue Natively
        student_queue = state_manager.get_student_queue()
        parent_stack = window.parentWidget()
        
        if student_queue:
            next_stu = student_queue.pop(0)
            state_manager.set_current_student(next_stu)
            state_manager.set_student_queue(student_queue)
            
            # Wipe affordance tracking state completely for the next child
            state_manager.current_path = []
            state_manager.set_affordance_level(1)
            
            try:
                from screens import greeting_screen
                if parent_stack:
                    greeting_ui = greeting_screen.get_ui()
                    parent_stack.addWidget(greeting_ui)
                    parent_stack.setCurrentWidget(greeting_ui)
            except ImportError: pass
        else:
            try:
                from screens import session_complete
                if parent_stack:
                    session_complete_ui = session_complete.get_ui()
                    parent_stack.addWidget(session_complete_ui)
                    parent_stack.setCurrentWidget(session_complete_ui)
            except ImportError: pass
