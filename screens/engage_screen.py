import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "engageUI.ui")

window = None
input_enabled = False
engage_data = {}

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
    print("[Engage Screen] Becoming active...")
    state_manager.set_current_screen("engage")
    
    task_data = state_manager.get_current_task()
    if not task_data or "engage" not in task_data:
        print("Error: No valid engage task found in state_manager.")
        window.title_label.setText("Error: Task not loaded.")
        return
        
    global input_enabled, engage_data
    input_enabled = False
    engage_data = task_data.get("engage", {})
    
    # 1. Populate Title
    window.title_label.setText(engage_data.get("task_title", "Let's Try Again!"))
    
    # 2. Populate Media (Prior Knowledge Recall)
    media_url = engage_data.get("video_url", "")
    if media_url:
        abs_media_path = os.path.join(project_root, media_url)
        if os.path.exists(abs_media_path):
            pixmap = QPixmap(abs_media_path)
            window.media_label.setPixmap(pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            window.media_label.setText("🌟\n[Media File Missing]")
    else:
        window.media_label.setText("🌟\n[No Visual Prompt Provided]")
        
    # Placeholder for Step 48
    window.robot_text_label.setText("🤖 Establishing warm emotional context...")

# Placeholders for future steps
def play_second_speech():
    pass
    
def enable_input():
    pass

def handle_key_press(action):
    pass
