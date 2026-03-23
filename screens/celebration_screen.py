import os
import random
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer
from core.state_manager import state_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "celebrationUI.ui")

window = None

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
    student_name = state_manager.current_student
    if not student_name:
        student_name = "Superstar"
        print("[Celebration Screen] Warning: No active student found in state manager.")
        
    # 2. Pick Random Encouragement Phrase
    phrases = [
        "Wow, {name}! You got it right! You're a superstar! 🌟",
        "Amazing job, {name}! That is totally correct! 🎉",
        "Fantastic work, {name}! You are so smart! 💡",
        "You nailed it, {name}! You are a genius! ✨"
    ]
    
    selected_phrase = random.choice(phrases).format(name=student_name)
    
    # 3. Update UI Text
    window.celebration_text.setText(selected_phrase)
    
    # 4. Robot Speech Stub (Filter out emojis for speech engine)
    clean_speech = selected_phrase.replace('🌟', '').replace('🎉', '').replace('💡', '').replace('✨', '')
    print(f"🤖 ROBOT SPEAKS: \"{clean_speech.strip()}\"")
    
    # TODO Step 20: Visual gamified reward timer will trigger here
