import os
import random
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.sound_manager import sound_manager
from core.animations import apply_pulse_glow
from core.timer_widget import EmojiTimerWidget
from core.voice_manager import VoiceManager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "evaluateLevel1UI.ui")

window = None
input_enabled = False
active_animations = []
evaluate_timer = None
key_mapping = {"1": "op1", "2": "op2", "3": "op3", "4": "op4"}
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
        
        # Bind the navigator lifecycle hook
        window.on_show = on_show
        
    return window

def on_show():
    global evaluate_timer, active_animations, input_enabled, key_mapping
    level = state_manager.get_affordance_level()
    
    print(f"[Evaluate Screen] Becoming active at Affordance Level {level}...")
    state_manager.set_current_screen("evaluate")
    
    # 0. Clean Resets
    if evaluate_timer:
        evaluate_timer.stop()
    for anim in active_animations:
        anim.stop()
        
    sound_manager.stop_bgm()
        
    active_animations.clear()
    input_enabled = False
    
    # 1. Fetch Task Data
    task_data = state_manager.get_current_task()
    if not task_data or "evaluate" not in task_data:
        print("Error: No valid evaluate task found in state_manager.")
        window.question_label.setText("Error: Task not loaded.")
        return
        
    eval_data = task_data["evaluate"]
    
    # 2. Set Question Text
    title_text = eval_data.get("task_title", "Evaluation Phase")
    desc_text = eval_data.get("task_description", "What was the question?")
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    
    if level >= 3:
        # Level 3 Affective Affordance: Personalized context and Escape Hatch control
        window.question_label.setText(f"Okay {student_name}, {desc_text.lower()}\n(Press S to Skip)")
    else:
        window.question_label.setText(f"{title_text}: {desc_text}\nUse the numbers on your keyboard to pick an option!")
    
    # 3. Apply Option Cards
    mc_words = eval_data.get("multiple_choices_word", {})
    mc_images = eval_data.get("multiple_choices_images", {})
    correct_option_key = eval_data.get("correct_option")
    
    img_size = 220
    if level >= 2:
        window.card_3.hide()
        window.card_4.hide()
        
        if level == 2:
            img_size = 350
            # Physical Affordance: Layout Ambience L2
            window.setStyleSheet("QWidget#EvaluateLevel1 { background-color: #1A237E; border: 15px solid #FFD600; border-radius: 10px; font-family: 'Nunito', sans-serif; }")
            window.question_label.setStyleSheet("font-size: 34px; font-weight: bold; color: #00838F; background-color: white; border-radius: 20px; padding: 15px;")
            for c in [window.card_1, window.card_2]:
                c.setStyleSheet("QFrame { background-color: white; border-radius: 25px; border: 4px solid #4DD0E1; }")
            for t in [window.text_1, window.text_2]:
                t.setStyleSheet("font-size: 24px; font-weight: bold; color: #00838F; border: none; background: transparent;")
            for k in [window.key_1, window.key_2]:
                k.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #00BCD4; border-radius: 12px; padding: 5px; margin: 0px 40px;")
                
            sound_manager.play_bell()
            sound_manager.play_bgm("arcade")
        else:
            # Level 3: Maximum Accessible High-Contrast
            img_size = 400
            window.setStyleSheet("QWidget#EvaluateLevel1 { background-color: #000000; font-family: 'Nunito', sans-serif; border: none; }")
            window.question_label.setStyleSheet("font-size: 40px; font-weight: bold; color: #FFFF00; background-color: black; border-radius: 20px; padding: 15px; border: 2px solid #FFFF00;")
            for c in [window.card_1, window.card_2]:
                c.setStyleSheet("QFrame { background-color: #000000; border-radius: 25px; border: 6px solid #FFFF00; }")
            for t in [window.text_1, window.text_2]:
                t.setStyleSheet("font-size: 32px; font-weight: bold; color: #FFFF00; border: none; background: transparent;")
            for k in [window.key_1, window.key_2]:
                k.setStyleSheet("font-size: 26px; font-weight: bold; color: black; background-color: #FFFF00; border-radius: 12px; padding: 5px; margin: 0px 40px;")
        
        # Pick 1 correct and 1 random distractor
        distractors = [k for k in mc_words.keys() if k != correct_option_key]
        distractor_key = random.choice(distractors) if distractors else "op1"
        
        chosen_keys = [correct_option_key, distractor_key]
        random.shuffle(chosen_keys)
        
        key_mapping = {
            "1": chosen_keys[0],
            "2": chosen_keys[1]
        }
    else:
        # Reset to base pastel cyan natively
        window.setStyleSheet("QWidget#EvaluateLevel1 { background-color: #E0F7FA; font-family: 'Nunito', sans-serif; border: none; }")
        window.question_label.setStyleSheet("font-size: 34px; font-weight: bold; color: #00838F; background-color: white; border-radius: 20px; padding: 15px;")
        for c in [window.card_1, window.card_2, window.card_3, window.card_4]:
            c.setStyleSheet("QFrame { background-color: white; border-radius: 25px; border: 4px solid #4DD0E1; }")
        for t in [window.text_1, window.text_2, window.text_3, window.text_4]:
            t.setStyleSheet("font-size: 24px; font-weight: bold; color: #00838F; border: none; background: transparent;")
        for k in [window.key_1, window.key_2, window.key_3, window.key_4]:
            k.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #00BCD4; border-radius: 12px; padding: 5px; margin: 0px 40px;")
            
        window.card_3.show()
        window.card_4.show()
        img_size = 220
        key_mapping = {"1": "op1", "2": "op2", "3": "op3", "4": "op4"}
    
    def setup_card(idx, text_widget, img_widget):
        physical_key = str(idx)
        if physical_key not in key_mapping:
            # Hide card if not part of the current key_mapping
            text_widget.parentWidget().hide()
            return
            
        text_widget.parentWidget().show() # Ensure it's visible if it's mapped
        json_key = key_mapping[physical_key]
        
        # Ensure text is populated
        text_widget.setText(mc_words.get(json_key, ""))
        
        # Ensure image is dynamically pulled from disk (or fallback)
        img_path = mc_images.get(json_key, "")
        if img_path:
            abs_img_path = os.path.join(project_root, img_path)
            if os.path.exists(abs_img_path):
                pixmap = QPixmap(abs_img_path)
                # Keep aspect ratio safely bounded inside the grid
                img_widget.setPixmap(pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img_widget.setText("\n\n[Image Missing]\n\n")
        else:
            img_widget.clear() # Clear any previous image if no new one
                
    setup_card(1, window.text_1, window.img_1)
    setup_card(2, window.text_2, window.img_2)
    setup_card(3, window.text_3, window.img_3)
    setup_card(4, window.text_4, window.img_4)

    # 4. Bind Animations
    for anim in active_animations:
        anim.stop()
    active_animations.clear()
    
    # Identify exactly which physical frame contains the correct payload
    correct_physical_key = next((k for k, v in key_mapping.items() if v == correct_option_key), None)
    
    print(f"\n[TESTING CHEAT] 🎯 The correct answer for this task is: Option {correct_physical_key} (Press '{correct_physical_key}')\n")
    
    if level >= 3:
        # Level 3 Physical Affordance: Aggressively Spotlight ONLY the correct answer
        if correct_physical_key == "1":
            active_animations.append(apply_pulse_glow(window.card_1))
        elif correct_physical_key == "2":
            active_animations.append(apply_pulse_glow(window.card_2))
    else:
        # Standard L1/L2 Layout: Pulse all available interactive objects evenly
        if "1" in key_mapping: active_animations.append(apply_pulse_glow(window.card_1))
        if "2" in key_mapping: active_animations.append(apply_pulse_glow(window.card_2))
        if "3" in key_mapping: active_animations.append(apply_pulse_glow(window.card_3))
        if "4" in key_mapping: active_animations.append(apply_pulse_glow(window.card_4))

    # 5. Robot Speech & Input Delay
    input_enabled = False
    
    speech_start = eval_data.get("speech_start", "Let's try a task.")
    desc_text = eval_data.get("task_description", "")
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    
    # Mathematical Speech Cadence offset
    if level >= 3:
        # Step 38 & 39: Level 3 Speech Simplification, Cadence, & personalization
        speech_text = f"Okay {student_name}, look carefully! {speech_start} {desc_text}".strip()
        print(f"🤖 ROBOT SPEAKS [SLOW RATE -30%]: \"{speech_text}\"")
        voice_manager.speak(speech_text, f"eval_l3_{student_name}_{task_data.get('task_id', 'id')}")
        
        # Slower 1.5 words-per-second computational cadence
        words_count = len(speech_text.split())
        delay_ms = max(3000, int((words_count / 1.8) * 1000))
    else:
        speech_text = f"{student_name}, {speech_start} {desc_text} Press the number to select your answer.".strip()
        print(f"🤖 ROBOT SPEAKS: \"{speech_text}\"")
        voice_manager.speak(speech_text, f"eval_l1_{student_name}_{task_data.get('task_id', 'id')}")
        
        # Standard 2.5 words-per-second computational cadence
        words_count = len(speech_text.split())
        delay_ms = max(2000, int((words_count / 1.8) * 1000))
    
    print(f"Delaying keyboard input for {delay_ms}ms to allow speech to strictly finish...")
    QTimer.singleShot(delay_ms, enable_input)

def enable_input():
    global input_enabled, evaluate_timer
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)
    print("[Evaluate Screen L1] Speech finished. Keyboard input enabled.")
    
    # Spin up the evaluation timer seamlessly after speech finishes
    evaluate_timer = EmojiTimerWidget(
        label_widget=window.timer_label,
        total_seconds=20,
        clock_count=10,
        timeout_callback=on_timer_expire
    )
    evaluate_timer.start()

def on_timer_expire():
    global input_enabled
    if not input_enabled:
        return
        
    input_enabled = False
    print("[Evaluate Screen L1] Timer EXPIRED! ⏰ (Treating as Incorrect)")
    
    global active_animations
    for anim in active_animations:
        anim.stop()
        
    sound_manager.stop_bgm()
        
    # Delegate terminal routing completely accurately into isolated flow controller natively
    try:
        from core.flow_controller import flow_controller
        parent_stack = window.parentWidget()
        if parent_stack:
            flow_controller.on_timeout(parent_stack)
    except ImportError: pass
        
def handle_key_press(action):
    global input_enabled, evaluate_timer, key_mapping, active_animations
    if not input_enabled:
        return
        
    # L2 Control Affordance: Break
    if action == "BREAK" and state_manager.get_affordance_level() >= 2:
        input_enabled = False
        print("[Evaluate Screen] Student pressed BREAK. Suspending session...")
        
        # Cease physics
        if evaluate_timer:
            evaluate_timer.stop()
        for anim in active_animations:
            anim.stop()
            
        sound_manager.stop_bgm()
            
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.on_break(parent_stack)
        except ImportError: pass
        return
        
    # L3 Control Affordance: Skip
    if action == "SKIP" and state_manager.get_affordance_level() >= 3:
        input_enabled = False
        print("[Evaluate Screen] Student pressed SKIP. Logging and skipping student...")
        
        # Cease physics
        if evaluate_timer:
            evaluate_timer.stop()
        for anim in active_animations:
            anim.stop()
            
        sound_manager.stop_bgm()
            
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.on_skip(parent_stack)
        except ImportError: pass
        return
        
    # Normal Mapping Validation
    if action not in key_mapping:
        return
        
    # Lock out further inputs immediately
    input_enabled = False
    print(f"[Evaluate Screen] Student pressed physical key {action}.")
    
    # Stop distracting animations and audio gracefully
    for anim in active_animations:
        anim.stop()
        
    sound_manager.stop_bgm()
        
    # Highlight the chosen card visually via StyleSheet manipulation
    card_map = {
        "1": window.card_1,
        "2": window.card_2,
        "3": window.card_3,
        "4": window.card_4
    }
    
    selected_card = card_map.get(action)
    if selected_card:
        selected_card.setStyleSheet("QFrame { background-color: #FFF176; border-radius: 25px; border: 6px solid #FF9F1C; }")
        
    # Validation logic
    task_data = state_manager.get_current_task()
    eval_data = task_data.get("evaluate", {}) if task_data else {}
    correct_option = eval_data.get("correct_option")
    
    # Map physical key stroke natively back to JSON structure
    selected_option = key_mapping[action]
    
    if evaluate_timer:
        evaluate_timer.stop()
    
    if selected_option == correct_option:
        print(f"[Evaluate Screen] Answer VALIDATION: CORRECT! 🎉")
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.on_correct_answer(parent_stack)
        except ImportError: pass
            
    else:
        print(f"[Evaluate Screen] Answer VALIDATION: INCORRECT! ❌")
        
        # 1. Fetch dynamic emotional encouragement sequence and speak natively on this screen!
        from core.dialogue import DialoguePool
        student_name = state_manager.get_current_student() or "friend"
        current_level = state_manager.get_affordance_level()
        dialogue_category = f"incorrect_L{current_level}"
        encouragement_speech = DialoguePool.get_phrase(dialogue_category, student_name)
        
        print(f"🤖 ROBOT ENCOURAGES: \"{encouragement_speech}\"")
        voice_manager.speak(encouragement_speech, f"eval_encourage_{student_name}")
        
        # 2. Delay the cascade escalation to give the Robot time to finish speaking.
        clean_speech = encouragement_speech.replace('🌟', '').replace('🎉', '').replace('💡', '').replace('✨', '')
        words_count = len(clean_speech.split())
        delay_ms = max(2000, int((words_count / 1.8) * 1000))
        
        from PySide6.QtCore import QTimer
        def proceed_to_incorrect_cascade():
            try:
                from core.flow_controller import flow_controller
                parent_stack = window.parentWidget()
                if parent_stack:
                    flow_controller.on_incorrect_answer(parent_stack)
            except ImportError: pass
            
        QTimer.singleShot(delay_ms, proceed_to_incorrect_cascade)
