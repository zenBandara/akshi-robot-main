import os
import json
import pygame

from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QSizePolicy
)

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer, Qt


current_dir = os.path.dirname(__file__)
ui_path = os.path.join(current_dir, "evaluationUI.ui")

window = None
timer = None
timer_label = None
animations = []

task_data = None
correct_option = None


def get_ui():

    global window

    loader = QUiLoader()
    file = QFile(ui_path)

    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    setup_ui()

    return window


def setup_ui():

    global window
    global timer_label

    window.skip_button.setFixedHeight(70)
    window.break_button.setFixedHeight(70)

    window.skip_button.setMinimumWidth(120)
    window.break_button.setMinimumWidth(120)

    window.skip_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    window.break_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    window.volume.hide()

    timer_label = QLabel()
    timer_label.setAlignment(Qt.AlignCenter)
    timer_label.setStyleSheet("font-size:32px;")

    timer_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    window.controlLayout.insertWidget(1, timer_label)

    setup_animation()


def setup_animation():

    global animations

    animations.append(apply_pulse_glow(window.mcq_image01))
    animations.append(apply_pulse_glow(window.mcq_image02))
    animations.append(apply_pulse_glow(window.mcq_image03))
    animations.append(apply_pulse_glow(window.mcq_image04))


def apply_pulse_glow(widget):

    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    pulse = QPropertyAnimation(effect, b"opacity")
    pulse.setDuration(800)
    pulse.setStartValue(0.5)
    pulse.setKeyValueAt(0.5, 0.7)
    pulse.setEndValue(1.0)
    pulse.setLoopCount(-1)
    pulse.setEasingCurve(QEasingCurve.InOutQuad)

    glow = QPropertyAnimation(widget, b"styleSheet")
    glow.setDuration(900)

    glow.setKeyValueAt(
        0.0,
        "background-color:#FFD166; border-radius:30px; border:5px solid #FF9F1C;"
    )

    glow.setKeyValueAt(
        0.5,
        "background-color:#FFF176; border-radius:30px; border:5px solid #FF6F00;"
    )

    glow.setKeyValueAt(
        1.0,
        "background-color:#FFD166; border-radius:30px; border:5px solid #FF9F1C;"
    )

    glow.setLoopCount(-1)

    group = QParallelAnimationGroup()
    group.addAnimation(pulse)
    group.addAnimation(glow)

    group.start()

    return group


def setup_timer():

    global timer
    global timer_label

    alarm_path = os.path.join(current_dir, "audio", "alarm.mp3")

    pygame.mixer.init()

    alarm_sound = None
    alarm_channel = None

    if os.path.exists(alarm_path):
        alarm_sound = pygame.mixer.Sound(alarm_path)

    def play_alarm():
        nonlocal alarm_channel
        if alarm_sound:
            alarm_channel = alarm_sound.play(loops=-1)

    def stop_alarm():
        nonlocal alarm_channel
        if alarm_channel:
            alarm_channel.stop()

    clock_total = 15
    task_seconds = 20
    remaining_clocks = clock_total

    timer = QTimer(window)

    fade_effect = QGraphicsOpacityEffect()
    timer_label.setGraphicsEffect(fade_effect)

    fade_anim = QPropertyAnimation(fade_effect, b"opacity")
    fade_anim.setDuration(350)
    fade_anim.setStartValue(1.0)
    fade_anim.setEndValue(0.25)

    def update_clock():
        nonlocal remaining_clocks

        if remaining_clocks <= 0:
            timer.stop()
            stop_alarm()
            return

        fade_anim.start()

    def remove_clock():
        nonlocal remaining_clocks

        remaining_clocks -= 1

        timer_label.setText(" ".join(["🕒"] * remaining_clocks))
        fade_effect.setOpacity(1.0)

        if remaining_clocks == 0:
            timer.stop()
            stop_alarm()

    fade_anim.finished.connect(remove_clock)

    interval = int((task_seconds / clock_total) * 1000)

    timer_label.setText(" ".join(["🕒"] * remaining_clocks))

    timer.timeout.connect(update_clock)
    timer.start(interval)

    play_alarm()


# ---------------- LESSON START ----------------

def start_lesson(lesson_id):

    global task_data
    global correct_option

    print("Evaluation started for lesson:", lesson_id)

    # check json file existence
    json_path = os.path.join(current_dir, "Tasks", "task_jsons", f"{lesson_id}.json")

    if not os.path.exists(json_path):
        print("Task JSON not found:", json_path)
        return

    print("Task JSON found:", json_path)

    # load json
    with open(json_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    print("Loaded JSON:")
    print(task_data)

    # read correct option
    correct_option = task_data["evaluate"]["correct_option"]

    print("Correct option:", correct_option)

    setup_timer()

    # enable keyboard listener
    window.keyPressEvent = handle_key_press


# ---------------- KEYBOARD INPUT ----------------

def handle_key_press(event):

    global correct_option

    key = event.text()

    if key not in ["1", "2", "3", "4"]:
        return

    selected = f"op{key}"

    print("Selected option:", selected)

    if selected == correct_option:

        print("Correct answer")

        import engage
        engage_screen = engage.get_ui()

        parent_stack = window.parentWidget()

        if parent_stack:
            parent_stack.addWidget(engage_screen)
            parent_stack.setCurrentWidget(engage_screen)

    else:

        print("Incorrect answer. Encouragement message.")