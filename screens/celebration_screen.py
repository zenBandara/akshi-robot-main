import os
import random
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.state_manager import state_manager
from core.voice_manager import VoiceManager

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
    
    # 1. Fetch exact Student Name
    student_name = state_manager.get_current_student()
    display_name = str(student_name).capitalize() if student_name else "Superstar"
    if not student_name:
        print("[Celebration Screen] Warning: No active student found in state manager.")
        
    # 2. Pick Random Encouragement Phrase
    from core.dialogue import DialoguePool
    selected_phrase = DialoguePool.get_phrase("correct", display_name)
    
    # 3. Update UI Text
    window.celebration_text.setText(selected_phrase)
    
    # 4. Robot Speech Stub (Filter out emojis for speech engine)
    clean_speech = selected_phrase.replace('🌟', '').replace('🎉', '').replace('💡', '').replace('✨', '')
    clean_speech_str = clean_speech.strip()
    print(f"🤖 ROBOT SPEAKS: \"{clean_speech_str}\"")
    voice_manager.speak(clean_speech_str, f"celebrate_{student_name}")
    
    # 5. Gamified Reward statically (Level 1 Affective Affordance)
    # The blinking animation has been removed based on user feedback.
    
    # 6. Show reward for 6 seconds, then move on
    print("[Celebration Screen] Displaying gamified reward for 6 seconds...")
    QTimer.singleShot(6000, end_celebration)

def end_celebration():
    global reward_anim
    if reward_anim:
        reward_anim.stop()
        
    print("[Celebration Screen] Celebration timeout reached.")
    
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
    
    # 8. Delegate structurally safely to the Global Session Logic sequence
    import core.session_logic as session_logic
    session_logic.next_student()
