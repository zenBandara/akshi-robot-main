import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager

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
    
    student_name = state_manager.get_current_student() or "friend"
    speech_start = elab_data.get("speech_start", "Oops! Let's try this one more time...")
    question_text = elab_data.get("task_description", "Which option is correct?")
    
    speech_text = f"{student_name}, {speech_start} {question_text} Press the number to select your answer."
    
    print(f"🤖 ROBOT SPEAKS: \"{speech_text}\"")
    voice_manager.speak(speech_text, f"elaborate_question_{task_data.get('task_id', 'id')}_{student_name}")
    
    # Calculate rough delay based on text length (~2.5 words per second)
    words_count = len(speech_text.split())
    delay_ms = max(2000, int((words_count / 1.8) * 1000))
    
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
    
    # Highlight the chosen card visually via StyleSheet manipulation
    card_map = {
        "1": window.card_1,
        "2": window.card_2,
        "3": window.card_3,
        "4": window.card_4
    }
    
    selected_card = card_map.get(action)
    
    # Validation logic
    task_data = state_manager.get_current_task()
    elab_data = task_data.get("elaborate", {}) if task_data else {}
    correct_option = elab_data.get("correct_option")
    
    # Map physical key stroke natively back to JSON structure
    key_mapping = {"1": "op1", "2": "op2", "3": "op3", "4": "op4"}
    selected_option = key_mapping.get(action)
    
    student_name = state_manager.get_current_student() or "friend"
    from core.flow_controller import flow_controller
    
    if selected_option == correct_option:
        print("[Elaborate Screen] Answer VALIDATION: CORRECT! 🎉")
        if selected_card:
            selected_card.setStyleSheet("QFrame { background-color: #C8E6C9; border-radius: 25px; border: 6px solid #4CAF50; }")
            
        speech = "Great job! Now let's try the real question again."
        print(f"🤖 ROBOT SPEAKS: \"{speech}\"")
        voice_manager.speak(speech, f"elaborate_correct_{student_name}")
        
        # Advance FlowController natively to evaluate_L2 (Cascade Index 2)
        flow_controller.cascade_index = 2
        state_manager.set_affordance_level(2)
        state_manager.current_stage = "evaluate_L2"
        
        # Wait 3000ms for audio to resolve cleanly
        delay_ms = 3000
        def proceed_to_eval():
            try:
                from core.navigator import navigator
                navigator.navigate_to("evaluate")
            except Exception as e:
                print(f"Warning: Could not transition back to evaluate screen. {e}")
                
        QTimer.singleShot(delay_ms, proceed_to_eval)
        
    else:
        print("[Elaborate Screen] Answer VALIDATION: INCORRECT! ❌")
        if selected_card:
            selected_card.setStyleSheet("QFrame { background-color: #FFCCBC; border-radius: 25px; border: 6px solid #E64A19; }")
            
        from core.dialogue import DialoguePool
        encouragement_speech = DialoguePool.get_phrase("incorrect_L1", student_name)
        print(f"🤖 ROBOT ENCOURAGES: \"{encouragement_speech}\"")
        voice_manager.speak(encouragement_speech, f"elaborate_wrong_{student_name}")
        
        # Advance FlowController completely bypassing L2 straight to explain (Cascade Index 3)
        flow_controller.cascade_index = 3
        state_manager.current_stage = "explain"
        
        clean_speech = encouragement_speech.replace('🌟', '').replace('🎉', '').replace('💡', '').replace('✨', '')
        words_count = len(clean_speech.split())
        delay_ms = max(2000, int((words_count / 1.8) * 1000))
        
        def proceed_to_explain():
            try:
                from core.navigator import navigator
                navigator.navigate_to("explain")
            except Exception as e:
                print(f"Warning: Could not transition back to explain screen. {e}")
                
        QTimer.singleShot(delay_ms, proceed_to_explain)
