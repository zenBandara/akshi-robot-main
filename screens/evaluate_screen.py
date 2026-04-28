"""
Evaluate Screen — "Akshi's Enchanted Forest" Edition
=====================================================
Replaces the plain white QUiLoader-based evaluation with a QPainter
game world (sky, sun, clouds, hills, flowers, owl + speech bubble,
signpost answer cards).

All existing logic (timers, motivation nudges, speech, cascade) is UNCHANGED.
Only the visual layer is swapped.
"""

import os
import random
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.sound_manager import sound_manager
from core.timer_widget import EmojiTimerWidget
from core.voice_manager import VoiceManager
from components.evaluate_game import EvaluateGameWidget

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)

window = None
game_widget = None
timer_label = None
input_enabled = False
active_animations = []
evaluate_timer = None
motivation_timer = None
motivation_given = False
key_mapping = {"1": "op1", "2": "op2", "3": "op3", "4": "op4"}
voice_manager = VoiceManager()

def get_ui():
    global window, game_widget, timer_label
    if window is None:
        window = QWidget()
        window.setObjectName("EvaluateLevel1")

        layout = QVBoxLayout(window)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        game_widget = EvaluateGameWidget()
        layout.addWidget(game_widget)

        # Hidden timer label (EmojiTimerWidget needs a QLabel reference)
        timer_label = QLabel("")
        timer_label.setVisible(False)
        layout.addWidget(timer_label)

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
        return

    eval_data = task_data["evaluate"]

    # 2. Build question text
    desc_text = eval_data.get("task_description", "What was the question?")
    student_name = str(state_manager.get_current_student() or "friend").capitalize()

    if level >= 3:
        question_display = f"{desc_text}\n(Press S to Skip)"
    elif level == 2:
        question_display = f"{desc_text}\n(Press B to take a Break 🌿)"
    else:
        question_display = desc_text

    # 3. Build option cards
    mc_words = eval_data.get("multiple_choices_word", {})
    mc_images = eval_data.get("multiple_choices_images", {})
    correct_option_key = eval_data.get("correct_option")

    if level >= 2:
        # L2/L3: Pick 1 correct + 1 random distractor
        distractors = [k for k in mc_words.keys() if k != correct_option_key]
        distractor_key = random.choice(distractors) if distractors else "op1"

        chosen_keys = [correct_option_key, distractor_key]
        random.shuffle(chosen_keys)

        key_mapping = {
            "1": chosen_keys[0],
            "2": chosen_keys[1]
        }

        if level == 2:
            sound_manager.play_bell()
            sound_manager.play_bgm("arcade")
    else:
        key_mapping = {"1": "op1", "2": "op2", "3": "op3", "4": "op4"}

    # 4. Build options list for the game widget
    options = []
    for physical_key in sorted(key_mapping.keys()):
        json_key = key_mapping[physical_key]
        label = mc_words.get(json_key, f"Option {physical_key}")

        img_path = mc_images.get(json_key, "")
        pixmap = None
        if img_path:
            abs_img_path = os.path.join(project_root, img_path)
            if os.path.exists(abs_img_path):
                pixmap = QPixmap(abs_img_path)

        options.append({
            "key": json_key,
            "label": label,
            "pixmap": pixmap,
        })

    # 5. Set the game widget data
    game_widget.set_question(question_display, options, level, student_name)

    # Identify which physical key is correct (for debug)
    correct_physical_key = next((k for k, v in key_mapping.items() if v == correct_option_key), None)
    print(f"\n[TESTING CHEAT] 🎯 The correct answer for this task is: Option {correct_physical_key} (Press '{correct_physical_key}')\n")

    # 6. Robot Speech & Input Delay
    input_enabled = False

    speech_start = eval_data.get("speech_start", "Let's try a task.")
    desc_text = eval_data.get("task_description", "")

    if level >= 3:
        speech_text = f"Okay {student_name}, look carefully! {speech_start} {desc_text}".strip()
        print(f"🤖 ROBOT SPEAKS [SLOW RATE -30%]: \"{speech_text}\"")
        delay_ms = voice_manager.speak(speech_text, f"eval_l3_{student_name}_{task_data.get('task_id', 'id')}")

        print(f"Enabling keyboard input immediately to allow for speech interruption.")
        enable_input()

        print(f"Delaying visual clock countdown for {delay_ms}ms...")
        if evaluate_timer:
            def start_both_timers():
                evaluate_timer.start()
                if motivation_timer:
                    motivation_timer.start()
            QTimer.singleShot(delay_ms, start_both_timers)
    else:
        speech_text = f"{student_name}, {speech_start} {desc_text}".strip()
        print(f"🤖 ROBOT SPEAKS INTRO: \"{speech_text}\"")
        delay_ms = voice_manager.speak(speech_text, f"eval_intro_{student_name}_{task_data.get('task_id', 'id')}")

        keys_to_speak = sorted(list(key_mapping.keys()))
        options_speech = eval_data.get("multiple_choices_speech", {})

        def speak_next_option(idx=0):
            if not input_enabled:
                return

            if idx >= len(keys_to_speak):
                game_widget.clear_highlight()
                print(f"Option explanations finished. Starting timer.")
                if evaluate_timer:
                    evaluate_timer.start()
                if motivation_timer:
                    motivation_timer.start()
                return

            game_widget.clear_highlight()
            current_key = keys_to_speak[idx]
            op_code = key_mapping[current_key]

            # Highlight the current option in the game widget
            game_widget.highlight_answer(op_code, correct=True)

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
        label_widget=timer_label,
        total_seconds=180,
        clock_count=18,
        timeout_callback=on_timer_expire,
        progress_callback=lambda p: game_widget.set_timer_progress(p)
    )

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
    # Use level-specific motivation
    if level >= 3:
        nudge = DialoguePool.get_phrase("motivation_nudge_l3", student_name)
        print(f"⏰ [1 MIN NUDGE L3] 🤖 ROBOT MOTIVATES (GENTLE): \"{nudge}\"")
    elif level == 2:
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

    if level >= 3:
        # ── L3: Student is too unresponsive, skip entirely to next student ──
        from core.dialogue import DialoguePool
        print(f"[Evaluate Screen] ⏭️ L3 timeout → Skipping student {student_name}!")
        skip_speech = DialoguePool.get_phrase("skip_l3", student_name)
        delay_ms = voice_manager.speak(skip_speech, f"timeout_skip_{student_name}")

        def skip_student():
            try:
                from core.flow_controller import flow_controller
                parent_stack = window.parentWidget()
                if parent_stack:
                    flow_controller.on_skip(parent_stack)
            except Exception as e:
                print(f"[Evaluate Screen] Error skipping student: {e}")

        QTimer.singleShot(delay_ms, skip_student)
    elif level == 2:
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

    # Stop timers
    if motivation_timer:
        motivation_timer.stop()
        motivation_timer = None
    for anim in active_animations:
        anim.stop()

    sound_manager.stop_bgm()

    # Highlight the chosen card in the game widget
    selected_option = key_mapping[action]
    task_data = state_manager.get_current_task()
    eval_data = task_data.get("evaluate", {}) if task_data else {}
    correct_option = eval_data.get("correct_option")

    is_correct = (selected_option == correct_option)
    game_widget.highlight_answer(selected_option, correct=is_correct)

    if evaluate_timer:
        evaluate_timer.stop()

    if is_correct:
        print(f"[Evaluate Screen] Answer VALIDATION: CORRECT! 🎉")
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.on_correct_answer(parent_stack)
        except ImportError: pass

    else:
        print(f"[Evaluate Screen] Answer VALIDATION: INCORRECT! ❌")

        from core.dialogue import DialoguePool
        student_name = state_manager.get_current_student() or "friend"
        current_level = state_manager.get_affordance_level()
        dialogue_category = f"incorrect_L{current_level}"
        encouragement_speech = DialoguePool.get_phrase(dialogue_category, student_name)

        print(f"🤖 ROBOT ENCOURAGES: \"{encouragement_speech}\"")
        delay_ms = voice_manager.speak(encouragement_speech, f"eval_encourage_{student_name}")

        def proceed_to_incorrect_cascade():
            try:
                from core.flow_controller import flow_controller
                parent_stack = window.parentWidget()
                if parent_stack:
                    flow_controller.on_incorrect_answer(parent_stack)
            except ImportError: pass

        QTimer.singleShot(delay_ms, proceed_to_incorrect_cascade)
