import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes
from core.stream_control import set_frame_streaming

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "elaborateUI.ui")

window = None
input_enabled = False
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
    print("[Elaborate Screen Guided Mode] Becoming active...")
    state_manager.set_current_screen("elaborate")

    # Keep real frames streaming during scaffolding.
    try:
        set_frame_streaming(True, reason="elaborate")
    except Exception as e:
        print("[Elaborate Screen] Error resuming frames:", e)
    
    # Hide the obsolete timer
    window.timer_label.hide()
    
    # 1. Fetch Task Data
    task_data = state_manager.get_current_task()
    if not task_data or "elaborate" not in task_data:
        print("Error: No valid elaborate task found in state_manager.")
        window.question_label.setText("Error: Task not loaded.")
        return
        
    elab_data = task_data.get("elaborate", {})
    student_name = state_manager.get_current_student() or "friend"
    
    # 2. Set Question Text
    window.question_label.setText(elab_data.get("task_description", "Let's review this together!"))
    
    # 3. Apply Option Cards
    mc_words = elab_data.get("multiple_choices_word", {})
    mc_images = elab_data.get("multiple_choices_images", {})
    mc_speech = elab_data.get("multiple_choices_speech", {})
    correct_option = elab_data.get("correct_option", "op1")
    
    # 4. Beautiful Styling setup
    for k in [window.key_1, window.key_2, window.key_3, window.key_4]:
        k.setStyleSheet("min-width: 50px; max-width: 50px; min-height: 50px; max-height: 50px; font-size: 26px; font-weight: bold; color: white; background-color: #BA68C8; border-radius: 25px; margin: 0px 10px 10px 0px;")
        try:
            k.parentWidget().layout().setAlignment(k, Qt.AlignRight | Qt.AlignBottom)
        except Exception: pass
        
    for img in [window.img_1, window.img_2, window.img_3, window.img_4]:
        img.setStyleSheet("background-color: white; border-radius: 20px; padding: 10px;")
        try:
            img.parentWidget().layout().setAlignment(img, Qt.AlignCenter)
        except Exception: pass
        
    def reset_all_highlights():
        for c in [window.card_1, window.card_2, window.card_3, window.card_4]:
            c.setStyleSheet("QFrame { background-color: white; border-radius: 25px; border: 4px solid #CE93D8; }")
            
    reset_all_highlights()
        
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

    # 5. Robot Explanation Loop
    global input_enabled
    input_enabled = False
    voice_manager.stop()
    
    get_robot_eyes().set_expression("encouraging")
    
    speech_start = elab_data.get("speech_start", "Let's review this together!")
    keys_to_speak = ["1", "2", "3", "4"]
    key_mapping = {"1": "op1", "2": "op2", "3": "op3", "4": "op4"}
    
    def highlight_card(action, is_correct=False):
        card_map = {
            "1": window.card_1,
            "2": window.card_2,
            "3": window.card_3,
            "4": window.card_4
        }
        selected_card = card_map.get(action)
        if selected_card:
            if is_correct:
                selected_card.setStyleSheet("QFrame { background-color: #C8E6C9; border-radius: 25px; border: 6px solid #4CAF50; }")
            else:
                selected_card.setStyleSheet("QFrame { background-color: #FFF176; border-radius: 25px; border: 6px solid #FF9F1C; }")

    def end_elaboration():
        if not input_enabled:
            return
        # Read final correct answer sequence
        get_robot_eyes().set_expression("surprised")
        reset_all_highlights()
        
        # Reverse map correct_option ("op1") back to key ("1")
        reverse_mapping = {v: k for k, v in key_mapping.items()}
        correct_key = reverse_mapping.get(correct_option, "1")
        highlight_card(correct_key, is_correct=True)
        
        final_speech = elab_data.get("correct_option_speech", "This is the correct answer! Say 'Okay' to try the real quiz again!")
        print(f"🤖 ROBOT SPEAKS CONCLUSION: \"{final_speech}\"")
        delay_ms = voice_manager.speak(final_speech, f"elaborate_{student_name}_conclusion")

    def speak_next_option(idx=0):
        if not input_enabled:
            return
            
        if idx >= len(keys_to_speak):
            end_elaboration()
            return

        reset_all_highlights()
        current_key = keys_to_speak[idx]
        op_code = key_mapping[current_key]

        highlight_card(current_key)

        # Look up explicit explanation
        op_speech = mc_speech.get(op_code, f"Let's look at option {current_key}.")
        
        print(f"🤖 ROBOT GUIDES OPTION {current_key}: \"{op_speech}\"")
        op_delay_ms = voice_manager.speak(op_speech, f"elaborate_opt_{student_name}_{op_code}")

        QTimer.singleShot(op_delay_ms + 400, lambda: speak_next_option(idx + 1))

    # Start Introduction
    print(f"🤖 ROBOT SPEAKS INTRO: \"{speech_start}\"")
    intro_delay = voice_manager.speak(speech_start, f"elaborate_intro_{student_name}")
    QTimer.singleShot(intro_delay + 300, speak_next_option)
    
    print(f"[Elaborate Screen Guided Mode] Enabling keyboard input immediately to allow interruption.")
    enable_input()

def enable_input():
    global input_enabled
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)
    print("[Elaborate Screen Guided Mode] Explanation complete. Keyboard hardware inputs enabled.")

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action in ["ENTER", "YES"]:
        input_enabled = False
        voice_manager.stop()
        get_robot_eyes().set_expression("default")
        
        print("[Elaborate Screen] Student said OKAY/YES! Re-evaluating via FlowController Native Cascade.")
        
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.advance_cascade(parent_stack)
        except ImportError: pass
