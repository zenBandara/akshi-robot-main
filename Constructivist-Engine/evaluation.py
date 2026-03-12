import sys
import os
import pygame

from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QLabel,
    QSizePolicy
)

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer, Qt

app = QApplication(sys.argv)

current_dir = os.path.dirname(__file__)
ui_path = os.path.join(current_dir, "evaluationUI.ui")

loader = QUiLoader()
file = QFile(ui_path)

if not file.open(QFile.ReadOnly):
    print("Cannot open UI file:", ui_path)
    sys.exit()

window = loader.load(file)
file.close()


# ---------------- Stabilize Skip and Break Buttons ----------------

window.skip_button.setFixedHeight(70)
window.break_button.setFixedHeight(70)

window.skip_button.setMinimumWidth(120)
window.break_button.setMinimumWidth(120)

window.skip_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
window.break_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


# ---------------- Pulse + Glow Animation ----------------

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


# ---------------- Replace Volume Slider With Clock Timer ----------------

window.volume.hide()

timer_label = QLabel()
timer_label.setAlignment(Qt.AlignCenter)
timer_label.setStyleSheet("font-size:32px;")

timer_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

window.controlLayout.insertWidget(1, timer_label)


# ---------------- Alarm Sound (Modified Section) ----------------


alarm_path = os.path.join(current_dir, "audio", "alarm.mp3")

pygame.mixer.init()

alarm_sound = None
alarm_channel = None

if os.path.exists(alarm_path):
    alarm_sound = pygame.mixer.Sound(alarm_path)
else:
    print("Alarm file not found:", alarm_path)


def play_alarm():
    global alarm_channel
    if alarm_sound:
        alarm_channel = alarm_sound.play(loops=-1)  # loop forever


def stop_alarm():
    global alarm_channel
    if alarm_channel:
        alarm_channel.stop()


# ---------------- Clock Timer ----------------

clock_total = 15
task_seconds = 20

remaining_clocks = clock_total

timer = QTimer(window)


# ---------------- Fade Effect ----------------

fade_effect = QGraphicsOpacityEffect()
timer_label.setGraphicsEffect(fade_effect)

fade_anim = QPropertyAnimation(fade_effect, b"opacity")
fade_anim.setDuration(350)
fade_anim.setStartValue(1.0)
fade_anim.setEndValue(0.25)
fade_anim.setEasingCurve(QEasingCurve.InOutQuad)


def start_clock_timer():

    global remaining_clocks

    remaining_clocks = clock_total

    timer_label.setText(" ".join(["🕒"] * remaining_clocks))

    interval = int((task_seconds / clock_total) * 1000)

    timer.timeout.connect(update_clock)
    timer.start(interval)

    # start alarm looping
    play_alarm()


def update_clock():

    global remaining_clocks

    if remaining_clocks <= 0:
        timer.stop()
        stop_alarm()
        return

    fade_anim.start()


def remove_clock():

    global remaining_clocks

    remaining_clocks -= 1

    timer_label.setText(" ".join(["🕒"] * remaining_clocks))

    fade_effect.setOpacity(1.0)

    if remaining_clocks == 0:
        timer.stop()
        stop_alarm()


fade_anim.finished.connect(remove_clock)


# ---------------- UI Setup ----------------

window.show()
app.processEvents()

animations = []

animations.append(apply_pulse_glow(window.mcq_image01))
animations.append(apply_pulse_glow(window.mcq_image02))
animations.append(apply_pulse_glow(window.mcq_image03))
animations.append(apply_pulse_glow(window.mcq_image04))

start_clock_timer()

sys.exit(app.exec())