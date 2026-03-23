import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "elaborateUI.ui")

window = None
input_enabled = False

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
    print("[Elaborate Screen L1] Becoming active...")
    state_manager.set_current_screen("elaborate_L1")
    
    # 1. Fetch Task Data for Elaborate Stage
    task_data = state_manager.get_current_task()
    if not task_data or "elaborate" not in task_data:
        print("Error: No valid elaborate task found in state_manager.")
        window.question_label.setText("Error: Task not loaded.")
        return
        
    elab_data = task_data.get("elaborate", {})
    
    # 2. Set Question Text
    window.question_label.setText(elab_data.get("task_description", "Let's review this together!"))
    
    # 3. Apply Option Cards
    mc_words = elab_data.get("multiple_choices_word", {})
    mc_images = elab_data.get("multiple_choices_images", {})
    
    def setup_card(idx, text_widget, img_widget):
        key = f"op{idx}"
        text_widget.setText(mc_words.get(key, ""))
        
        img_path = mc_images.get(key, "")
        if img_path:
            abs_img_path = os.path.join(project_root, img_path)
            if os.path.exists(abs_img_path):
                pixmap = QPixmap(abs_img_path)
                img_widget.setPixmap(pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img_widget.setText("\n\n[Image Missing]\n\n")
                
    setup_card(1, window.text_1, window.img_1)
    setup_card(2, window.text_2, window.img_2)
    setup_card(3, window.text_3, window.img_3)
    setup_card(4, window.text_4, window.img_4)

    # 4. Robot Speech & Input Delay
    global input_enabled
    input_enabled = False
    
    speech_text = elab_data.get("speech_start", "Oops! Let's try this one more time...")
    print(f"🤖 ROBOT SPEAKS: \"{speech_text}\"")
    
    # Calculate rough delay based on text length (~2.5 words per second)
    words_count = len(speech_text.split())
    delay_ms = max(2000, int((words_count / 2.5) * 1000))
    
    print(f"[Elaborate Screen L1] Delaying keyboard input for {delay_ms}ms to let speech finish...")
    QTimer.singleShot(delay_ms, enable_input)

def enable_input():
    global input_enabled
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)
    print("[Elaborate Screen L1] Speech finished. Keyboard input enabled.")

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action not in ["1", "2", "3", "4"]:
        return
        
    # Lock out further inputs immediately
    input_enabled = False
    print(f"[Elaborate Screen L1] Student pressed key {action}. Review complete!")
    
    # Highlight the chosen card visually (Deep Purple border / Light Purple BG)
    card_map = {
        "1": window.card_1,
        "2": window.card_2,
        "3": window.card_3,
        "4": window.card_4
    }
    
    selected_card = card_map.get(action)
    if selected_card:
        selected_card.setStyleSheet("QFrame { background-color: #E1BEE7; border-radius: 25px; border: 6px solid #8E24AA; }")
        
    print("[Elaborate Screen L1] Transitioning back to Evaluate (Level 2)...")
    state_manager.set_affordance_level(2)
    
    try:
        from screens import evaluate_screen
        parent_stack = window.parentWidget()
        if parent_stack:
            evaluate_ui = evaluate_screen.get_ui()
            parent_stack.addWidget(evaluate_ui)
            parent_stack.setCurrentWidget(evaluate_ui)
    except ImportError:
        print("Warning: Could not transition back to evaluate screen.")
