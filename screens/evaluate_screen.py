import os
import random
import pygame
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.animations import apply_pulse_glow
from core.timer_widget import EmojiTimerWidget

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "evaluateLevel1UI.ui")

window = None
input_enabled = False
active_animations = []
evaluate_timer = None
arcade_bgm = None
key_mapping = {"1": "op1", "2": "op2", "3": "op3", "4": "op4"}

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
        
        # Safely init audio mixer
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as e:
            print(f"Warning: Audio mixer failed to initialize. {e}")
        
        # Bind the navigator lifecycle hook
        window.on_show = on_show
        
    return window

def on_show():
    global evaluate_timer, active_animations, input_enabled, key_mapping
    level = state_manager.get_affordance_level()
    
    print(f"[Evaluate Screen] Becoming active at Affordance Level {level}...")
    state_manager.set_current_screen("evaluate")
    
    # 0. Clean Resets
    global arcade_bgm
    if evaluate_timer:
        evaluate_timer.stop()
    for anim in active_animations:
        anim.stop()
    if arcade_bgm:
        arcade_bgm.stop()
        
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
    window.question_label.setText(eval_data.get("task_description", "What was the question?"))
    
    # 3. Apply Option Cards
    mc_words = eval_data.get("multiple_choices_word", {})
    mc_images = eval_data.get("multiple_choices_images", {})
    correct_option_key = eval_data.get("correct_option")
    
    img_size = 220
    if level >= 2:
        window.card_3.hide()
        window.card_4.hide()
        img_size = 350
        
        # Physical Affordance: Acoustic Bell & Layout Ambience
        window.setStyleSheet("QWidget#EvaluateLevel1 { background-color: #1A237E; border: 15px solid #FFD600; border-radius: 10px; font-family: 'Nunito', sans-serif; }")
        
        bell_path = os.path.join(project_root, "assets", "sounds", "bell.wav")
        if os.path.exists(bell_path):
            try:
                bell = pygame.mixer.Sound(bell_path)
                bell.set_volume(0.4)
                bell.play()
            except Exception as e:
                pass
                
        bgm_path = os.path.join(project_root, "assets", "sounds", "arcade_bgm.wav")
        if os.path.exists(bgm_path):
            try:
                arcade_bgm = pygame.mixer.Sound(bgm_path)
                arcade_bgm.set_volume(0.15)
                arcade_bgm.play(loops=-1)
            except Exception as e:
                pass
        
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
        # Reset to base pastel cyan
        window.setStyleSheet("QWidget#EvaluateLevel1 { background-color: #E0F7FA; font-family: 'Nunito', sans-serif; border: none; }")
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
    global active_animations
    for anim in active_animations:
        anim.stop()
    active_animations.clear()
    
    active_animations.append(apply_pulse_glow(window.card_1))
    active_animations.append(apply_pulse_glow(window.card_2))
    active_animations.append(apply_pulse_glow(window.card_3))
    active_animations.append(apply_pulse_glow(window.card_4))

    # 5. Robot Speech & Input Delay
    global input_enabled
    input_enabled = False
    
    speech_text = eval_data.get("speech_start", "Let's try a task.")
    print(f"🤖 ROBOT SPEAKS: \"{speech_text}\"")
    
    # Calculate rough delay based on text length (~2.5 words per second)
    words_count = len(speech_text.split())
    delay_ms = max(2000, int((words_count / 2.5) * 1000))
    
    print(f"Delaying keyboard input for {delay_ms}ms to allow speech to finish...")
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
    global input_enabled, arcade_bgm
    if not input_enabled:
        return
        
    input_enabled = False
    print("[Evaluate Screen L1] Timer EXPIRED! ⏰ (Treating as Incorrect)")
    
    global active_animations
    for anim in active_animations:
        anim.stop()
        
    if arcade_bgm:
        arcade_bgm.stop()
        
    # TODO: Trigger failure path via flow controller (Step 25+)
        
def handle_key_press(action):
    global input_enabled, evaluate_timer, key_mapping, arcade_bgm
    if not input_enabled:
        return
        
    if action not in key_mapping:
        return
        
    # Lock out further inputs immediately
    input_enabled = False
    print(f"[Evaluate Screen] Student pressed physical key {action}.")
    
    # Stop distracting animations and audio gracefully
    global active_animations, arcade_bgm
    for anim in active_animations:
        anim.stop()
    if arcade_bgm:
        arcade_bgm.stop()
        
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
        print(f"[Evaluate Screen] Answer VALIDATION: CORRECT! 🎉 (Level {state_manager.get_affordance_level()})")
        
        try:
            from screens import celebration_screen
            parent_stack = window.parentWidget()
            if parent_stack:
                celebration_ui = celebration_screen.get_ui()
                parent_stack.addWidget(celebration_ui)
                parent_stack.setCurrentWidget(celebration_ui)
        except ImportError:
            print("Warning: Could not transition to celebration screen.")
            
    else:
        print(f"[Evaluate Screen L1] Answer VALIDATION: INCORRECT! ❌ (Selected: {selected_option}, Expected: {correct_option})")
        # TODO: Trigger failure path (Step 25+ Elaborate Screen)
