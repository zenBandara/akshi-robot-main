import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "explainUI.ui")

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
        
    # Placeholder for Step 34 (Speech)
    window.robot_text_label.setText("🤖 Generating explanation...")
