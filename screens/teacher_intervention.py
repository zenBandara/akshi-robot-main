"""
Teacher Intervention Screen
=============================
A clean screen for the teacher to take over.
Shows the student name, the question, and a "Press C" prompt.
Matches the app's existing light pastel + blue typography design language.
"""

import os
import math
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient,
    QFont, QPen
)
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)

window = None
game_widget = None
input_enabled = False
voice_manager = VoiceManager()


class TeacherInterventionWidget(QWidget):
    """Painted teacher intervention screen matching the app's light/blue design theme."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.tick = 0

        self.student_name = ""
        self.question_text = ""
        self.affordance_level = 3
        self.path_taken = []

        # Subtle animation (15 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(66)

    def load_data(self, student_name, task_data, level=3, path=None):
        self.student_name = student_name
        self.affordance_level = level
        self.path_taken = path or []
        eval_data = task_data.get("evaluate", {}) if task_data else {}
        self.question_text = eval_data.get("task_description", "Question not available")
        self.update()

    def _animate(self):
        self.tick += 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        self._draw_bg(p, w, h)
        self._draw_title_card(p, w, h)
        self._draw_message(p, w, h)
        self._draw_question_card(p, w, h)
        self._draw_robot_speech(p, w, h)
        self._draw_action_button(p, w, h)

        p.end()

    # ─── BACKGROUND — matches #E3F2FD (teacher intervention original) ───
    def _draw_bg(self, p, w, h):
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor(227, 242, 253))   # #E3F2FD
        bg.setColorAt(1, QColor(207, 232, 252))    # slightly deeper at bottom
        p.fillRect(0, 0, w, h, bg)

    # ─── TITLE CARD — white rounded card with bold blue text ───
    def _draw_title_card(self, p, w, h):
        margin = 50
        card_h = 90
        card_rect = QRectF(margin, 40, w - margin * 2, card_h)

        # White card with border — matches evaluateLevel1UI cards
        p.setPen(QPen(QColor(100, 181, 246), 4))   # #64B5F6 border
        p.setBrush(QColor(255, 255, 255))
        p.drawRoundedRect(card_rect, 20, 20)

        # Title text — matches #1565C0 bold blue
        p.setFont(QFont("Helvetica", 36, QFont.Bold))
        p.setPen(QColor(21, 101, 192))             # #1565C0
        p.drawText(card_rect, Qt.AlignCenter, "Teacher Time! 👩‍🏫")

    # ─── MESSAGE — "Student needs help" ───
    def _draw_message(self, p, w, h):
        margin = 70
        msg_rect = QRectF(margin, 155, w - margin * 2, 50)

        p.setFont(QFont("Helvetica", 26))
        p.setPen(QColor(13, 71, 161))              # #0D47A1
        p.drawText(msg_rect, Qt.AlignCenter | Qt.TextWordWrap,
                   f"Dear teacher, {self.student_name} could use a little extra help! 😊")

    # ─── QUESTION CARD — the main feature ───
    def _draw_question_card(self, p, w, h):
        margin = 50
        card_y = 230
        card_h = int(h * 0.30)
        card_rect = QRectF(margin, card_y, w - margin * 2, card_h)

        # White card — same style as evaluate question_label: #F8FAFC bg, rounded
        p.setPen(QPen(QColor(226, 232, 240), 4))   # #E2E8F0 border
        p.setBrush(QColor(248, 250, 252))           # #F8FAFC
        p.drawRoundedRect(card_rect, 20, 20)

        inner_margin = 30

        # "Question" label — small, muted
        p.setFont(QFont("Helvetica", 13))
        p.setPen(QColor(100, 116, 139))             # muted slate
        p.drawText(QRectF(margin + inner_margin, card_y + 16, 200, 22),
                   Qt.AlignLeft, "📝  Question for this student:")

        # Separator line
        line_y = card_y + 46
        p.setPen(QPen(QColor(226, 232, 240), 1))
        p.drawLine(int(margin + inner_margin), int(line_y),
                   int(w - margin - inner_margin), int(line_y))

        # Question text — big, bold, deep blue — matches #1A237E from evaluateLevel1UI
        p.setFont(QFont("Helvetica", 28, QFont.Bold))
        p.setPen(QColor(26, 35, 126))               # #1A237E
        question_rect = QRectF(margin + inner_margin, line_y + 14,
                               w - margin * 2 - inner_margin * 2,
                               card_h - 70)
        p.drawText(question_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                   self.question_text)

    # ─── ROBOT SPEECH — italic, green, matches other screens ───
    def _draw_robot_speech(self, p, w, h):
        speech_y = int(h * 0.62)
        p.setFont(QFont("Helvetica", 20))
        p.setPen(QColor(21, 101, 192))              # #1565C0 italic style
        speech_rect = QRectF(50, speech_y, w - 100, 50)
        p.drawText(speech_rect, Qt.AlignCenter | Qt.TextWordWrap,
                   "🤖  \"Let's ask teacher for some help!\"")

    # ─── ACTION BUTTON — blue rounded pill, matches #1976D2 system buttons ───
    def _draw_action_button(self, p, w, h):
        btn_w = 360
        btn_h = 60
        btn_x = w // 2 - btn_w // 2
        btn_y = int(h * 0.77)

        btn_rect = QRectF(btn_x, btn_y, btn_w, btn_h)

        # Blue button — #1976D2 matching all other action buttons in the app
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(25, 118, 210))            # #1976D2
        p.drawRoundedRect(btn_rect, 15, 15)

        # Button text
        p.setFont(QFont("Helvetica", 22, QFont.Bold))
        p.setPen(QColor(255, 255, 255))
        p.drawText(btn_rect, Qt.AlignCenter, "Teacher, say 'Okay' to continue")

        # Hint below
        p.setFont(QFont("Helvetica", 14))
        p.setPen(QColor(100, 116, 139))             # #64748B muted
        p.drawText(QRectF(0, btn_y + actual_h + 12, w, 30), Qt.AlignCenter,
                   "Please assist the student with the question above")


def get_ui():
    """Create the teacher intervention screen."""
    global window, game_widget
    if window is None:
        window = QWidget()
        window.setObjectName("TeacherInterventionScreen")

        layout = QVBoxLayout(window)
        layout.setContentsMargins(0, 0, 0, 0)

        game_widget = TeacherInterventionWidget()
        layout.addWidget(game_widget)

        window.on_show = on_show

    return window


def on_show():
    """Called when navigator switches to this screen."""
    global input_enabled
    print("[Teacher Intervention Screen] Becoming active...")
    state_manager.set_current_screen("teacher_intervention")
    get_robot_eyes().set_expression("sad")

    input_enabled = False

    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    task_data = state_manager.get_current_task()
    level = state_manager.get_affordance_level()
    path = getattr(state_manager, 'current_path', [])

    game_widget.load_data(student_name, task_data, level, path)

    speech_text = f"Let's ask teacher for some help! Don't worry {student_name}, you did great trying!"
    print(f"🤖 ROBOT SPEAKS [CHEERFUL ENCOURAGING TONE]: \"{speech_text}\"")
    delay_ms = voice_manager.speak(speech_text, f"teacher_intervention_{student_name}")

    print(f"Enabling keyboard input immediately to allow for speech interruption.")
    enable_input()


def enable_input():
    global input_enabled
    input_enabled = True
    print("[Teacher Intervention] Robot finished speaking. Waiting for Teacher Override (Key C).")
    keyboard_manager.register_handler(handle_key_press)


def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return

    if action == "ENTER":
        input_enabled = False
        voice_manager.stop()
        get_robot_eyes().set_expression("encouraging")
        print("[Teacher Intervention] Teacher pressed ENTER/CONTINUE. Logging complete cascade and resetting.")

        # Log Result (Complete Cascade Failure -> Teacher Assisted)
        task_data = state_manager.get_current_task()
        task_id = task_data.get("task_id", "unknown") if task_data else "unknown"
        student_id = state_manager.get_current_student() or "unknown"

        if not hasattr(state_manager, 'current_path') or not state_manager.current_path:
            state_manager.current_path = [
                "evaluate_L1", "elaborate", "evaluate_L2", "explain",
                "evaluate_L3", "explore", "evaluate_L3", "engage",
                "evaluate_L3", "teacher_intervention"
            ]

        log_data = {
            "student_id": student_id,
            "task_id": task_id,
            "result": "teacher_assisted",
            "affordance_level_reached": getattr(state_manager, "affordance_level", 3),
            "path_taken": state_manager.current_path
        }

        if not hasattr(state_manager, 'session_logs'):
            state_manager.session_logs = []
        state_manager.session_logs.append(log_data)

        try:
            from core import firebase
            firebase.log_event(log_data)
        except ImportError: pass

        print(f"[Teacher Intervention] LOGGED FINAL TASK RESULT: {log_data}")

        # Log to RL Database
        try:
            import core.database as database
            session_id = state_manager.get_current_session()
            student_name = state_manager.get_current_student() or "unknown"
            database.log_student_metric(session_id, student_name, "null", "teacher_intervention")
        except Exception as db_err:
            print(f"[Teacher Intervention] RL SQLite Telemetry Logging error: {db_err}")

        # After teacher intervention, phase is identified as 'elaborate' (most scaffolded)
        from core.flow_controller import flow_controller
        student_name = state_manager.get_current_student() or "unknown"
        flow_controller.identified_phase = "elaborate"
        flow_controller.progression_state = "CONFIRMING"
        flow_controller.baseline_confirms = 0
        flow_controller._save_student_state(student_name)
        
        state_manager.current_path = []
        state_manager.set_affordance_level(1)
        
        get_robot_eyes().set_expression("default")
        print("[Teacher Intervention] Phase set to 'elaborate'. Moving to next student...")
        import core.session_logic as session_logic
        session_logic.next_student()
