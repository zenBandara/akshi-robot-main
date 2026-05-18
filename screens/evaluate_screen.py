"""
Evaluate Screen — "Ginglu's Enchanted Forest" Edition
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
from components.robot_eyes import get_robot_eyes
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

# ── Sequential YES/NO presentation state ──
current_presenting_idx = -1   # Which option index is currently highlighted (-1 = not presenting)
presentation_keys = []        # Ordered list of physical keys being presented
awaiting_yes_no = False       # True when robot finished explaining and is waiting for YES/NO
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
    get_robot_eyes().set_expression("thinking")

    # Resume sending real frames to backend as the task is starting
    try:
        import json
        with open("ginglu-the-robot/calibration_command.json", "w") as f:
            json.dump({"type": "resume_frames"}, f)
    except Exception as e:
        print("[Evaluate Screen] Error resuming frames:", e)

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
        question_display = f"{desc_text}\n(Say 'Skip' to Skip)"
    elif level == 2:
        question_display = f"{desc_text}\n(Say 'Break' to take a Break 🌿)"
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

    # ── All levels now use the sequential YES/NO presentation ──
    speech_template = "{name}, " + f"{speech_start} {desc_text}".strip()
    print(f"🤖 ROBOT SPEAKS INTRO: \"{speech_template.replace('{name}', student_name)}\"")
    delay_ms = voice_manager.speak_with_name(speech_template, student_name, f"eval_intro_{student_name}_{task_data.get('task_id', 'id')}")

    enable_input()

    # Begin sequential option presentation after intro finishes
    QTimer.singleShot(delay_ms + 300, lambda: present_option(0))

def present_option(idx):
    """Highlight option at index `idx`, explain it, then ask YES/NO."""
    global current_presenting_idx, presentation_keys, awaiting_yes_no
    global key_mapping, input_enabled

    if not input_enabled:
        return

    presentation_keys = sorted(list(key_mapping.keys()))
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    task_data = state_manager.get_current_task()
    eval_data = task_data.get("evaluate", {}) if task_data else {}
    options_speech = eval_data.get("multiple_choices_speech", {})

    if idx >= len(presentation_keys):
        # Reached the end without finding the correct answer
        print(f"[Evaluate Screen] Exhausted all options without correct selection. Treating as INCORRECT.")
        
        # User requested: if we reach the end (e.g. said NO to everything), mark the last answer red.
        if len(presentation_keys) > 0:
            last_key = presentation_keys[-1]
            game_widget.highlight_answer(key_mapping[last_key], correct=False)
            
        awaiting_yes_no = False
        current_presenting_idx = -1
        _process_answer(is_correct=False)
        return

    current_presenting_idx = idx
    awaiting_yes_no = False  # Not yet — wait for speech to finish

    game_widget.clear_highlight()
    game_widget.set_focus_mode(False)
    current_key = presentation_keys[idx]
    op_code = key_mapping[current_key]

    # Highlight this option in BLUE to indicate it's the current one being asked
    game_widget.highlight_answer(op_code, correct="present")
    get_robot_eyes().set_expression("encouraging")

    # Speak the option explanation + ask YES/NO
    op_speech = options_speech.get(op_code, f"Option {int(current_key)}.")
    ask_speech = f"{op_speech} Is this your answer? Say yes or no."

    print(f"🤖 ROBOT ASKS OPTION {current_key}: \"{ask_speech}\"")
    op_delay_ms = voice_manager.speak(ask_speech, f"eval_ask_{student_name}_{op_code}")

    # Enable YES/NO input AFTER the robot finishes speaking
    def unlock_input():
        global awaiting_yes_no
        if input_enabled and current_presenting_idx == idx:
            awaiting_yes_no = True
            print(f"[Evaluate Screen] Waiting for YES/NO on option {current_key}...")
            
            # ── LEVEL 3 FOCUS DIMMING ──
            if state_manager.get_affordance_level() >= 3:
                game_widget.set_focus_mode(True)

    QTimer.singleShot(op_delay_ms + 200, unlock_input)

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
    get_robot_eyes().set_expression("encouraging")
    student_name = state_manager.get_current_student() or "friend"
    level = state_manager.get_affordance_level()

    from core.dialogue import DialoguePool
    # Use level-specific motivation
    if level >= 3:
        nudge_template, nudge_name = DialoguePool.get_template("motivation_nudge_l3", student_name)
        print(f"⏰ [1 MIN NUDGE L3] 🤖 ROBOT MOTIVATES (GENTLE): \"{nudge_template.format(name=nudge_name)}\"")
    elif level == 2:
        nudge_template, nudge_name = DialoguePool.get_template("motivation_nudge_l2", student_name)
        print(f"⏰ [1 MIN NUDGE L2] 🤖 ROBOT MOTIVATES (STRONG): \"{nudge_template.format(name=nudge_name)}\"")
    else:
        nudge_template, nudge_name = DialoguePool.get_template("motivation_nudge", student_name)
        print(f"⏰ [1 MIN NUDGE] 🤖 ROBOT MOTIVATES: \"{nudge_template.format(name=nudge_name)}\"")
    voice_manager.speak_with_name(nudge_template, nudge_name, f"motivation_{student_name}")

def on_timer_expire():
    """Called at 3 minutes — L1: escalate to kinesthetic, L2: rabbit jump break."""
    global input_enabled, motivation_timer
    if not input_enabled:
        return

    input_enabled = False
    level = state_manager.get_affordance_level()
    print(f"[Evaluate Screen] ⏰ 3-MINUTE TIMER EXPIRED at Level {level}!")
    get_robot_eyes().set_expression("sad")

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
        skip_template, skip_name = DialoguePool.get_template("skip_l3", student_name)
        delay_ms = voice_manager.speak_with_name(skip_template, skip_name, f"timeout_skip_{student_name}")

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
        timeout_template = "Hey {name}! I think you need some energy! Let's do something super fun!"
        delay_ms = voice_manager.speak_with_name(timeout_template, student_name, f"timeout_break_{student_name}")

        def go_to_break():
            try:
                from core.navigator import navigator
                navigator.navigate_to("break")
            except Exception as e:
                print(f"[Evaluate Screen] Error navigating to break: {e}")

        QTimer.singleShot(delay_ms, go_to_break)
    else:
        # ── L1: Route to Water Break Screen ──
        if motivation_given:
            timeout_template = "That's okay {name}! I think you might need a little rest!"
        else:
            timeout_template = "Hey {name}, it looks like you could use a small break!"
        delay_ms = voice_manager.speak_with_name(timeout_template, student_name, f"timeout_3min_{student_name}")

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
    global current_presenting_idx, awaiting_yes_no, presentation_keys
    if not input_enabled:
        return

    # L2 Control Affordance: Break
    if action == "BREAK" and state_manager.get_affordance_level() >= 2:
        input_enabled = False
        awaiting_yes_no = False
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
        awaiting_yes_no = False
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

    # ── YES/NO Sequential Answer Flow ──
    if action == "YES" and awaiting_yes_no and current_presenting_idx >= 0:
        awaiting_yes_no = False
        voice_manager.stop()

        # Student said YES to the currently highlighted option
        current_key = presentation_keys[current_presenting_idx]
        selected_option = key_mapping[current_key]

        task_data = state_manager.get_current_task()
        eval_data = task_data.get("evaluate", {}) if task_data else {}
        correct_option = eval_data.get("correct_option")

        is_correct = (selected_option == correct_option)

        print(f"[Evaluate Screen] Student said YES to option {current_key} ({selected_option}). Correct: {is_correct}")

        if is_correct:
            # Highlight green and finish
            game_widget.highlight_answer(selected_option, correct=True)
            input_enabled = False
            current_presenting_idx = -1
            _process_answer(True)
        else:
            # Student said YES to a wrong answer! We found what they were thinking.
            # Mark it red permanently and immediately go to the incorrect cascade (next step).
            game_widget.mark_wrong(selected_option)
            print(f"[Evaluate Screen] ❌ Student confidently selected a wrong answer! Moving to incorrect cascade.")
            input_enabled = False
            current_presenting_idx = -1
            _process_answer(False)
        return

    if action == "NO" and awaiting_yes_no and current_presenting_idx >= 0:
        awaiting_yes_no = False
        voice_manager.stop()

        current_key = presentation_keys[current_presenting_idx]
        selected_option = key_mapping[current_key]

        print(f"[Evaluate Screen] Student said NO to option {current_key} ({selected_option}).")

        # Always move to the next option, even if they rejected the correct answer
        print(f"[Evaluate Screen] Moving to next option...")
        present_option(current_presenting_idx + 1)
        return


def _process_answer(is_correct):
    """Shared logic for processing a correct or incorrect answer."""
    global evaluate_timer, motivation_timer, active_animations

    # Stop timers
    if evaluate_timer:
        evaluate_timer.stop()
    if motivation_timer:
        motivation_timer.stop()
        motivation_timer = None
    for anim in active_animations:
        anim.stop()

    game_widget.set_focus_mode(False)
    sound_manager.stop_bgm()

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
        encourage_template, encourage_name = DialoguePool.get_template(dialogue_category, student_name)

        print(f"🤖 ROBOT ENCOURAGES: \"{encourage_template.format(name=encourage_name)}\"")
        delay_ms = voice_manager.speak_with_name(encourage_template, encourage_name, f"eval_encourage_{student_name}")

        def proceed_to_incorrect_cascade():
            try:
                from core.flow_controller import flow_controller
                parent_stack = window.parentWidget()
                if parent_stack:
                    flow_controller.on_incorrect_answer(parent_stack)
            except ImportError: pass

        QTimer.singleShot(delay_ms, proceed_to_incorrect_cascade)
