import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "evaluateLevel1UI.ui")

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
        
        # Bind the navigator lifecycle hook
        window.on_show = on_show
        
    return window

def on_show():
    print("[Evaluate Screen L1] Becoming active...")
    state_manager.set_current_screen("evaluate_L1")
    
    # 1. Fetch Task Data
    task_data = state_manager.current_task
    if not task_data or "evaluate" not in task_data:
        print("Error: No valid evaluate task found in state_manager.")
        window.question_label.setText("Error: Task not loaded.")
        return
        
    eval_data = task_data["evaluate"]
    
    # 2. Set Question Text
    window.question_label.setText(eval_data.get("task_description", "What was the question?"))
    
    # 3. Apply Option Cards
    mc_words = eval_data.get("multiple_choices_word", {})
    mc_images = eval_data.get("multiple_choices_images", {})
    
    def setup_card(idx, text_widget, img_widget):
        key = f"op{idx}"
        
        # Ensure text is populated
        text_widget.setText(mc_words.get(key, ""))
        
        # Ensure image is dynamically pulled from disk (or fallback)
        img_path = mc_images.get(key, "")
        if img_path:
            abs_img_path = os.path.join(project_root, img_path)
            if os.path.exists(abs_img_path):
                pixmap = QPixmap(abs_img_path)
                # Keep aspect ratio safely bounded inside the grid
                img_widget.setPixmap(pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img_widget.setText("\n\n[Image Missing]\n\n")
                
    setup_card(1, window.text_1, window.img_1)
    setup_card(2, window.text_2, window.img_2)
    setup_card(3, window.text_3, window.img_3)
    setup_card(4, window.text_4, window.img_4)
