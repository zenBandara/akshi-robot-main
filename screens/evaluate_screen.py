from PySide6.QtGui import QPixmap
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
    
    # 0. Clean Resets
    global evaluate_timer, active_animations, input_enabled
    if evaluate_timer:
        evaluate_timer.stop()
    for anim in active_animations:
        anim.stop()
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
    global input_enabled
    if not input_enabled:
        return
        
    input_enabled = False
    print("[Evaluate Screen L1] Timer EXPIRED! ⏰ (Treating as Incorrect)")
    
    global active_animations
    for anim in active_animations:
        anim.stop()
        
    # TODO: Trigger failure path via flow controller (Step 25+)
        
def handle_key_press(action):
    global input_enabled, evaluate_timer
    if not input_enabled:
        return
        
    if action not in ["1", "2", "3", "4"]:
        return
        
    # Lock out further inputs immediately
    input_enabled = False
    print(f"[Evaluate Screen L1] Student pressed key {action}.")
    
    # Stop distracting animations gracefully
    global active_animations
    for anim in active_animations:
        anim.stop()
        
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
    selected_option = f"op{action}"
    
    if evaluate_timer:
        evaluate_timer.stop()
    
    if selected_option == correct_option:
        print("[Evaluate Screen L1] Answer VALIDATION: CORRECT! 🎉")
        
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
