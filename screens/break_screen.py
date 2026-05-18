"""
🐰 Break Screen — "Bunny Jump Break"
======================================
A 3-act gamified break for Level 2 students who are unresponsive.

Act 1 (Story):    Robot tells the story, bunny appears
Act 2 (Activity): 45-second timer — student hops like a bunny
Act 3 (Return):   Waiting for student to press ENTER (60s auto-skip)
"""

import os
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.sound_manager import sound_manager
from core.voice_manager import VoiceManager
from core.dialogue import DialoguePool
from components.rabbit_break_game import RabbitBreakWidget
from components.robot_eyes import get_robot_eyes

voice_manager = VoiceManager()

window = None
game_widget = None
input_enabled = False


def get_ui():
    """Create the break screen with the RabbitBreakWidget as the central display."""
    global window, game_widget
    if window is None:
        window = QWidget()
        window.setObjectName("BreakScreen")
        window.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(window)
        layout.setContentsMargins(0, 0, 0, 0)

        game_widget = RabbitBreakWidget()
        layout.addWidget(game_widget)

        # Connect signals
        game_widget.activity_complete.connect(_on_activity_complete)
        game_widget.halfway_reached.connect(_on_halfway)
        game_widget.almost_done.connect(_on_almost_done)
        game_widget.return_timeout.connect(_on_return_timeout)
        game_widget.return_warning.connect(_on_return_warning)

        window.on_show = on_show

    return window


def on_show():
    """Entry point — called when navigator switches to this screen."""
    global input_enabled
    print("[Break Screen] 🐰 Rabbit Jump Break starting!")
    state_manager.set_current_screen("break")
    get_robot_eyes().set_expression("sleeping")

    input_enabled = False
    voice_manager.stop()
    sound_manager.stop_bgm()

    # Reset the game widget
    game_widget.reset()
    game_widget.set_phase("story")

    student_name = str(state_manager.get_current_student() or "friend").capitalize()

    # Play upbeat music
    try:
        sound_manager.play_bgm("arcade")
    except Exception:
        pass

    # Act 1: Robot tells the story
    story_template, story_name = DialoguePool.get_template("break_story", student_name)
    print(f"🤖 ROBOT SPEAKS (Break Story): \"{story_template.format(name=story_name)}\"")
    delay_ms = voice_manager.speak_with_name(story_template, story_name, f"break_story_{student_name}")

    # After story speech finishes → start activity timer
    QTimer.singleShot(delay_ms + 500, _start_activity)


def _start_activity():
    """Transition to Act 2 — start the 45-second activity timer."""
    global input_enabled
    print("[Break Screen] Act 2: Activity timer starting (45 seconds)!")
    get_robot_eyes().set_expression("encouraging")

    game_widget.set_phase("activity")
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)


def _on_halfway():
    """Called at ~22 seconds — halfway encouragement."""
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    speech_template = "Great hopping, {name}! You're halfway there! Keep going!"
    get_robot_eyes().set_expression("surprised")
    print(f"🤖 ROBOT SPEAKS (Halfway): \"{speech_template.replace('{name}', student_name)}\"")
    voice_manager.speak_with_name(speech_template, student_name, f"break_halfway_{student_name}")


def _on_almost_done():
    """Called at ~5 seconds remaining — hurry back!"""
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    speech_template = "Almost done, {name}! Hop back to your seat!"
    print(f"🤖 ROBOT SPEAKS (Almost Done): \"{speech_template.replace('{name}', student_name)}\"")
    voice_manager.speak_with_name(speech_template, student_name, f"break_almost_{student_name}")


def _on_activity_complete():
    """Activity timer finished — transition to Act 3 (Return)."""
    print("[Break Screen] Act 3: Activity complete! Waiting for student to press ENTER...")
    game_widget.set_phase("return")
    get_robot_eyes().set_expression("thinking")

    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    return_template, return_name = DialoguePool.get_template("break_return", student_name)
    print(f"🤖 ROBOT SPEAKS (Return): \"{return_template.format(name=return_name)}\"")
    voice_manager.speak_with_name(return_template, return_name, f"break_return_{student_name}")


def _on_return_warning():
    """Called at 15 seconds remaining in return phase — verbal hurry-up."""
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    hurry_template, hurry_name = DialoguePool.get_template("break_hurry", student_name)
    print(f"🤖 ROBOT SPEAKS (Hurry): \"{hurry_template.format(name=hurry_name)}\"")
    voice_manager.speak_with_name(hurry_template, hurry_name, f"break_hurry_{student_name}")


def _on_return_timeout():
    """Student never came back after 60 seconds — skip to next student."""
    global input_enabled
    if not input_enabled:
        return

    input_enabled = False
    game_widget.stop_all()
    sound_manager.stop_bgm()
    voice_manager.stop()

    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    print(f"[Break Screen] ⏰ Return timeout! {student_name} did not come back. Skipping student.")
    get_robot_eyes().set_expression("sad")

    skip_template = "Oh no, {name} didn't come back. Let's move on to the next friend!"
    delay_ms = voice_manager.speak_with_name(skip_template, student_name, f"break_skip_{student_name}")

    def skip_student():
        try:
            from core.flow_controller import flow_controller
            flow_controller.on_skip(window.parentWidget())
        except Exception as e:
            print(f"[Break Screen] Error skipping student: {e}")

    QTimer.singleShot(delay_ms, skip_student)


def handle_key_press(action):
    """Handle student key press during break."""
    global input_enabled
    if not input_enabled:
        return

    if action == "ENTER" and game_widget.phase == "return":
        # Student came back! Resume the cascade (retry L2 evaluation)
        input_enabled = False
        game_widget.stop_all()
        sound_manager.stop_bgm()
        voice_manager.stop()
        get_robot_eyes().set_expression("surprised")

        student_name = str(state_manager.get_current_student() or "friend").capitalize()
        welcome_template = "Yay {name}, welcome back! You're full of energy now! Let's try again!"
        print(f"🤖 ROBOT SPEAKS (Welcome Back): \"{welcome_template.replace('{name}', student_name)}\"")
        delay_ms = voice_manager.speak_with_name(welcome_template, student_name, f"break_welcome_{student_name}")

        def resume():
            try:
                from core.flow_controller import flow_controller
                flow_controller.resume_cascade(window.parentWidget())
            except Exception as e:
                print(f"[Break Screen] Error resuming cascade: {e}")

        QTimer.singleShot(delay_ms, resume)
