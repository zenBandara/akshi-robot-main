import os
import random
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.state_manager import state_manager
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes
from core.stream_control import set_frame_streaming

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "celebrationUI.ui")

window = None
reward_anim = None
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
    print("[Celebration Screen] Becoming active...")
    state_manager.set_current_screen("celebration")
    get_robot_eyes().set_expression("surprised")
    
    # Pause (send black frames) during celebration speech.
    try:
        set_frame_streaming(False, reason="celebration")
    except Exception as e:
        print("[Celebration Screen] Error pausing frames:", e)
    
    # 1. Fetch exact Student Name
    student_name = state_manager.get_current_student()
    display_name = str(student_name).capitalize() if student_name else "Superstar"
    if not student_name:
        print("[Celebration Screen] Warning: No active student found in state manager.")
        
    # 2. Pick Random Encouragement Phrase
    from core.dialogue import DialoguePool
    template, name = DialoguePool.get_template("correct", display_name)
    selected_phrase = template.format(name=name)
    
    # 3. Update UI Text
    window.celebration_text.setText(selected_phrase)
    
    # 4. Robot Speech Stub (Filter out emojis for speech engine)
    clean_template = template.replace('🌟', '').replace('🎉', '').replace('💡', '').replace('✨', '').replace('🚀', '').replace('🏆', '')
    clean_template = clean_template.strip()
    print(f"🤖 ROBOT SPEAKS: \"{clean_template.format(name=name)}\"")
    duration_ms = voice_manager.speak_with_name(clean_template, name, f"celebrate_{student_name}")
    
    # 5. Gamified Reward statically (Level 1 Affective Affordance)
    # The blinking animation has been removed based on user feedback.
    
    # 6. Wait directly exactly correlating to real physical text-to-speech lengths!
    print(f"[Celebration Screen] Displaying gamified reward sequentially synced to audio track ({duration_ms}ms)...")
    QTimer.singleShot(duration_ms, end_celebration)

def end_celebration():
    global reward_anim
    if reward_anim:
        reward_anim.stop()
        
    print("[Celebration Screen] Celebration timeout reached.")
    get_robot_eyes().set_expression("encouraging")
    
    # 7. Log the Result (Step 21)
    task_data = state_manager.get_current_task()
    task_id = task_data.get("task_id", "unknown") if task_data else "unknown"
    student_id = state_manager.get_current_student() or "unknown"
    
    log_data = {
        "student_id": student_id,
        "task_id": task_id,
        "result": "correct",
        "affordance_level_reached": state_manager.get_affordance_level(),
        "path_taken": getattr(state_manager, "current_path", ["evaluate_L1"])
    }
    
    # Cache log locally
    if not hasattr(state_manager, 'session_logs'):
        state_manager.session_logs = []
    state_manager.session_logs.append(log_data)
    
    # Dispatch to Firebase stub
    try:
        from core import firebase
        firebase.log_event(log_data)
    except ImportError:
        pass
        
    print(f"[Celebration Screen] LOGGED SUCCESS: {log_data}")
    
    # 8. Move to the next student in this round
    import core.session_logic as session_logic
    session_logic.next_student()
