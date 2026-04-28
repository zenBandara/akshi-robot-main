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
motivation_timer = None
motivation_given = False
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
    global evaluate_timer, active_animations, input_enabled, key_mapping, motivation_timer, motivation_given
    level = state_manager.get_affordance_level()
    
    print(f"[Evaluate Screen] Becoming active at Affordance Level {level}...")
    state_manager.set_current_screen("evaluate")
    
    # 0. Clean Resets
    if evaluate_timer:
        evaluate_timer.stop()
    if motivation_timer:
        motivation_timer.stop()
        motivation_timer = None
    motivation_given = False
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
    desc_text = eval_data.get("task_description", "What was the question?")
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    
    if level >= 3:
        # Level 3 Affective Affordance: Personalized context and Escape Hatch control
        window.question_label.setText(f"Okay {student_name}, {desc_text.lower()}\n(Press S to Skip)")
    elif level == 2:
        # Level 2 Control Affordance: Break Option
        window.question_label.setText(f"{desc_text}\n(Press B to take a Break 🌿)")
    else:
        window.question_label.setText(desc_text)
    
    # 3. Apply Option Cards
    mc_words = eval_data.get("multiple_choices_word", {})
    mc_images = eval_data.get("multiple_choices_images", {})
    correct_option_key = eval_data.get("correct_option")
    img_size = 130
    if level >= 2:
        window.card_3.hide()
        window.card_4.hide()
        
        if level == 2:
            img_size = 350
            # Level 2: Bright, engaging sky-blue theme — child-friendly & professional
            window.setStyleSheet("""
                QWidget#EvaluateLevel1 { 
                    background-color: #E3F2FD; 
                    font-family: 'Nunito', sans-serif; 
                }
            """)
            window.question_label.setStyleSheet("""
                font-size: 38px; 
                font-weight: 900; 
                color: #1565C0; 
                background-color: #FFFFFF; 
                border-radius: 25px; 
                padding: 20px;
                border: 3px solid #90CAF9;
            """)
            
            # Clean, large white cards with soft blue borders
            for c in [window.card_1, window.card_2, window.card_3, window.card_4]:
                c.setStyleSheet("""
                    QFrame { 
                        background-color: #FFFFFF; 
                        border-radius: 30px; 
                        border: 4px solid #90CAF9;
                    }
                    QFrame:hover { border: 4px solid #1976D2; }
                """)
                
            for k in [window.key_1, window.key_2]:
                k.setStyleSheet("""
                    min-width: 65px; max-width: 65px; 
                    min-height: 65px; max-height: 65px; 
                    font-size: 34px; font-weight: 900; 
                    color: #FFFFFF; 
                    background-color: #1976D2; 
                    border-radius: 32px; 
                    margin: 0px 20px 20px 0px;
                """)
                try:
                    k.parentWidget().layout().setAlignment(k, Qt.AlignRight | Qt.AlignBottom)
                except Exception: pass
                
            for img in [window.img_1, window.img_2]:
                img.setStyleSheet("background-color: transparent; padding: 15px;")
                try:
                    img.parentWidget().layout().setAlignment(img, Qt.AlignCenter)
                except Exception: pass
                
            sound_manager.play_bell()
            sound_manager.play_bgm("arcade")
        else:
            # Level 3: Warm peach/coral theme — maximum clarity, still child-friendly
            img_size = 400
            window.setStyleSheet("""
                QWidget#EvaluateLevel1 { 
                    background-color: #FFF3E0; 
                    font-family: 'Nunito', sans-serif; 
                }
            """)
            window.question_label.setStyleSheet("""
                font-size: 40px; 
                font-weight: bold; 
                color: #E65100; 
                background-color: #FFFFFF; 
                border-radius: 20px; 
                padding: 15px; 
                border: 3px solid #FFCC80;
            """)
            for c in [window.card_1, window.card_2, window.card_3, window.card_4]:
                c.setStyleSheet("""
                    QFrame { 
                        background-color: #FFFFFF; 
                        border-radius: 25px; 
                        border: 4px solid #FFCC80; 
                    }
                    QFrame:hover { border: 4px solid #FF9800; }
                """)
            for k in [window.key_1, window.key_2]:
                k.setStyleSheet("""
                    min-width: 60px; max-width: 60px; 
                    min-height: 60px; max-height: 60px; 
                    font-size: 32px; font-weight: bold; 
                    color: #FFFFFF; 
                    background-color: #FF9800; 
                    border-radius: 30px; 
                    margin: 0px 15px 15px 0px;
                """)
                try:
                    k.parentWidget().layout().setAlignment(k, Qt.AlignRight | Qt.AlignBottom)
                except Exception: pass
            for img in [window.img_1, window.img_2]:
                img.setStyleSheet("background-color: transparent; border-radius: 20px; padding: 10px;")
                try:
                    img.parentWidget().layout().setAlignment(img, Qt.AlignCenter)
                except Exception: pass
        
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
        # Reset to base pristine layout natively
        window.setStyleSheet("QWidget#EvaluateLevel1 { background-color: #FFFFFF; font-family: 'Nunito', sans-serif; border: none; }")
        window.question_label.setStyleSheet("font-size: 38px; font-weight: bold; color: #1A237E; background-color: #F8FAFC; border-radius: 20px; padding: 15px;")
        for c in [window.card_1, window.card_2, window.card_3, window.card_4]:
            c.setStyleSheet("QFrame { background-color: #F8FAFC; border-radius: 25px; border: 4px solid #E2E8F0; }")
        for k in [window.key_1, window.key_2, window.key_3, window.key_4]:
            k.setStyleSheet("min-width: 50px; max-width: 50px; min-height: 50px; max-height: 50px; font-size: 26px; font-weight: bold; color: white; background-color: #1976D2; border-radius: 25px; margin: 0px 10px 10px 0px;")
            try:
                k.parentWidget().layout().setAlignment(k, Qt.AlignRight | Qt.AlignBottom)
            except Exception: pass
            
        for img in [window.img_1, window.img_2, window.img_3, window.img_4]:
            img.setStyleSheet("background-color: white; border-radius: 20px; padding: 10px;")
            try:
                img.parentWidget().layout().setAlignment(img, Qt.AlignCenter)
            except Exception: pass
            
        window.card_3.show()
        window.card_4.show()
        img_size = 130
        key_mapping = {"1": "op1", "2": "op2", "3": "op3", "4": "op4"}
    
    def setup_card(idx, img_widget):
        physical_key = str(idx)
        if physical_key not in key_mapping:
            # Hide card if not part of the current key_mapping
            img_widget.parentWidget().hide()
            return
            
        img_widget.parentWidget().show() # Ensure it's visible if it's mapped
        json_key = key_mapping[physical_key]
        
        # We explicitly skip setting any text, relying PURELY on image recognition payload
        
        # Ensure image is dynamically pulled from disk (or fallback)
        img_path = mc_images.get(json_key, "")
        if img_path:
            abs_img_path = os.path.join(project_root, img_path)
            if os.path.exists(abs_img_path):
                pixmap = QPixmap(abs_img_path)
                
                # To prevent PySide6 image truncation bugs inside tight layouts, we measure the widget natively
                # If the widget isn't fully drawn yet, img_size is safe
                img_widget.setPixmap(pixmap.scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img_widget.setText("\n\n[Image Missing]\n\n")
        else:
            img_widget.clear() # Clear any previous image if no new one
                
    setup_card(1, window.img_1)
    setup_card(2, window.img_2)
    setup_card(3, window.img_3)
    setup_card(4, window.img_4)

    # 4. Bind Animations
    for anim in active_animations:
        anim.stop()
    active_animations.clear()
    
    # Identify exactly which physical frame contains the correct payload
    correct_physical_key = next((k for k, v in key_mapping.items() if v == correct_option_key), None)
    
    print(f"\n[TESTING CHEAT] 🎯 The correct answer for this task is: Option {correct_physical_key} (Press '{correct_physical_key}')\n")
    
    # PER USER FEEDBACK: 
    # All visual "blinking" / opacity pulsing animations have been strictly eradicated from this Screen!
    # The layout remains purely static to maintain a highly professional Apple-like interface for the kids.

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
        delay_ms = voice_manager.speak(speech_text, f"eval_l3_{student_name}_{task_data.get('task_id', 'id')}")
        
        print(f"Enabling keyboard input immediately to allow for speech interruption.")
        enable_input()
        
        # Delay timer start until after speech actually finishes
        print(f"Delaying visual clock countdown for {delay_ms}ms...")
        if evaluate_timer:
            def start_both_timers():
                evaluate_timer.start()
                if motivation_timer:
                    motivation_timer.start()
            QTimer.singleShot(delay_ms, start_both_timers)
    else:
        # For Level 1 and 2, step through each option, highlighting it and speaking it.
        speech_text = f"{student_name}, {speech_start} {desc_text}".strip()
        print(f"🤖 ROBOT SPEAKS INTRO: \"{speech_text}\"")
        delay_ms = voice_manager.speak(speech_text, f"eval_intro_{student_name}_{task_data.get('task_id', 'id')}")
        
        keys_to_speak = sorted(list(key_mapping.keys()))
        options_speech = eval_data.get("multiple_choices_speech", {})
        
        def reset_all_highlights():
            card_map = {
                "1": window.card_1,
                "2": window.card_2,
                "3": window.card_3,
                "4": window.card_4
            }
            for k in keys_to_speak:
                card = card_map.get(k)
                if card:
                    if level == 2:
                        card.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 30px; border: 4px solid #90CAF9; } QFrame:hover { border: 4px solid #1976D2; }")
                    else:
                        card.setStyleSheet("QFrame { background-color: #F8FAFC; border-radius: 25px; border: 4px solid #E2E8F0; }")

        def highlight_card(key):
            card_map = {
                "1": window.card_1,
                "2": window.card_2,
                "3": window.card_3,
                "4": window.card_4
            }
            selected_card = card_map.get(key)
            if selected_card:
                if level == 2:
                    selected_card.setStyleSheet("QFrame { background-color: #BBDEFB; border-radius: 30px; border: 6px solid #1565C0; }")
                else:
                    selected_card.setStyleSheet("QFrame { background-color: #FFF176; border-radius: 25px; border: 6px solid #FF9F1C; }")

        def speak_next_option(idx=0):
            # If user already pressed a key or timer expired, input_enabled becomes False
            if not input_enabled:
                return
                
            if idx >= len(keys_to_speak):
                reset_all_highlights()
                print(f"Option explanations finished. Starting timer.")
                if evaluate_timer:
                    evaluate_timer.start()
                if motivation_timer:
                    motivation_timer.start()
                return
                
            reset_all_highlights()
            current_key = keys_to_speak[idx]
            op_code = key_mapping[current_key]
            
            highlight_card(current_key)
            
            op_speech = options_speech.get(op_code, f"Option {current_key}.")
            instruction_speech = f"{op_speech} If you think the highlighted one is the answer, press number {current_key}."
            
            print(f"🤖 ROBOT SPEAKS OPTION {current_key}: \"{instruction_speech}\"")
            op_delay_ms = voice_manager.speak(instruction_speech, f"eval_opt_{student_name}_{op_code}")
            
            QTimer.singleShot(op_delay_ms + 400, lambda: speak_next_option(idx + 1))

        print(f"Enabling keyboard input allowing interruption.")
        enable_input()
        
        print("Starting introduction speech before options...")
        QTimer.singleShot(delay_ms + 300, speak_next_option)

def enable_input():
    global input_enabled, evaluate_timer, motivation_timer, motivation_given
    input_enabled = True
    motivation_given = False
    keyboard_manager.register_handler(handle_key_press)
    print("[Evaluate Screen L1] Speech finished. Keyboard input enabled.")
    
    # ── Main Timer: 3 MINUTES (180 seconds) total before auto-escalation ──
    evaluate_timer = EmojiTimerWidget(
        label_widget=window.timer_label,
        total_seconds=180,
        clock_count=18,
        timeout_callback=on_timer_expire
    )
    # The timer start will be triggered distinctly by QTimer.singleShot matching speech resolution
    
    # ── Motivation Timer: 1 MINUTE (60 seconds) nudge ──
    motivation_timer = QTimer()
    motivation_timer.setSingleShot(True)
    motivation_timer.setInterval(60_000)  # 60 seconds
    motivation_timer.timeout.connect(on_motivation_nudge)
    print("[Evaluate Screen] Motivation nudge scheduled at 60 seconds, timeout at 180 seconds.")

def on_motivation_nudge():
    """At 1 minute of no response, give the student an encouraging push."""
    global motivation_given
    if not input_enabled:
        return  # Student already answered
    
    motivation_given = True
    student_name = state_manager.get_current_student() or "friend"
    level = state_manager.get_affordance_level()
    
    from core.dialogue import DialoguePool
    # Use stronger L2 motivation when applicable
    if level >= 2:
        nudge = DialoguePool.get_phrase("motivation_nudge_l2", student_name)
        print(f"⏰ [1 MIN NUDGE L2] 🤖 ROBOT MOTIVATES (STRONG): \"{nudge}\"")
    else:
        nudge = DialoguePool.get_phrase("motivation_nudge", student_name)
        print(f"⏰ [1 MIN NUDGE] 🤖 ROBOT MOTIVATES: \"{nudge}\"")
    voice_manager.speak(nudge, f"motivation_{student_name}")

def on_timer_expire():
    """Called at 3 minutes — L1: escalate to kinesthetic, L2: rabbit jump break."""
    global input_enabled, motivation_timer
    if not input_enabled:
        return
        
    input_enabled = False
    level = state_manager.get_affordance_level()
    print(f"[Evaluate Screen] ⏰ 3-MINUTE TIMER EXPIRED at Level {level}!")
    
    # Stop motivation timer if it's still active
    if motivation_timer:
        motivation_timer.stop()
        motivation_timer = None
    
    if evaluate_timer:
        evaluate_timer.stop()
    
    global active_animations
    for anim in active_animations:
        anim.stop()
        
    sound_manager.stop_bgm()
    student_name = state_manager.get_current_student() or "friend"
    
    if level >= 2:
        # ── L2: Route to Rabbit Jump Break screen ──
        print(f"[Evaluate Screen] 🐰 L2 timeout → Rabbit Jump Break for {student_name}!")
        timeout_speech = f"Hey {student_name}! I think you need some energy! Let's do something super fun!"
        delay_ms = voice_manager.speak(timeout_speech, f"timeout_break_{student_name}")
        
        def go_to_break():
            try:
                from core.navigator import navigator
                navigator.navigate_to("break")
            except Exception as e:
                print(f"[Evaluate Screen] Error navigating to break: {e}")
        
        QTimer.singleShot(delay_ms, go_to_break)
    else:
        # ── L1: Normal cascade timeout (kinesthetic test) ──
        if motivation_given:
            timeout_speech = f"That's okay {student_name}! Let's try something different. We're going to do a fun activity instead!"
        else:
            timeout_speech = f"Oops {student_name}, looks like you need a little more help! Let's try a fun activity together!"
        delay_ms = voice_manager.speak(timeout_speech, f"timeout_3min_{student_name}")
        
        def transition_after_speech():
            try:
                from core.flow_controller import flow_controller
                parent_stack = window.parentWidget()
                if parent_stack:
                    flow_controller.on_timeout(parent_stack)
            except ImportError: pass
        
        QTimer.singleShot(delay_ms, transition_after_speech)
        
def handle_key_press(action):
    global input_enabled, evaluate_timer, key_mapping, active_animations, motivation_timer
    if not input_enabled:
        return
        
    # L2 Control Affordance: Break
    if action == "BREAK" and state_manager.get_affordance_level() >= 2:
        input_enabled = False
        voice_manager.stop()
        print("[Evaluate Screen] Student pressed BREAK. Suspending session...")
        
        # Cease physics
        if evaluate_timer:
            evaluate_timer.stop()
        if motivation_timer:
            motivation_timer.stop()
            motivation_timer = None
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
        voice_manager.stop()
        print("[Evaluate Screen] Student pressed SKIP. Logging and skipping student...")
        
        # Cease physics
        if evaluate_timer:
            evaluate_timer.stop()
        if motivation_timer:
            motivation_timer.stop()
            motivation_timer = None
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
    voice_manager.stop()
    print(f"[Evaluate Screen] Student pressed physical key {action}.")
    
    # Stop distracting animations, audio, and motivation timer gracefully
    if motivation_timer:
        motivation_timer.stop()
        motivation_timer = None
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
        delay_ms = voice_manager.speak(encouragement_speech, f"eval_encourage_{student_name}")
        
        from PySide6.QtCore import QTimer
        def proceed_to_incorrect_cascade():
            try:
                from core.flow_controller import flow_controller
                parent_stack = window.parentWidget()
                if parent_stack:
                    flow_controller.on_incorrect_answer(parent_stack)
            except ImportError: pass
            
        QTimer.singleShot(delay_ms, proceed_to_incorrect_cascade)
