"""
👩‍🏫 Teacher Intervention Screen
=================================
A gamified, playful screen that shows the teacher:
  - Which student needs help
  - The exact question and all answer options (with images)
  - The correct answer highlighted with a star
  - The learning path the student went through

Press [C] to continue to the next student.
"""

import os
import math
import random
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QRadialGradient, QLinearGradient,
    QFont, QPen, QPixmap, QPainterPath
)
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)

window = None
game_widget = None
input_enabled = False
voice_manager = VoiceManager()


class TeacherInterventionWidget(QWidget):
    """Full-screen painted widget for the teacher intervention screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.tick = 0

        # Data holders
        self.student_name = ""
        self.question_text = ""
        self.correct_option = ""
        self.options = []  # list of {"key": "op1", "label": "Left Arrow", "pixmap": QPixmap or None, "is_correct": bool}
        self.path_taken = []

        # Decorative particles
        self.sparkles = []

        # Animation timer (20 FPS — lightweight)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(50)

    def load_task_data(self, student_name, task_data, path_taken=None):
        """Populate with the current evaluation question."""
        self.student_name = student_name
        self.path_taken = path_taken or []
        self.options = []

        eval_data = task_data.get("evaluate", {}) if task_data else {}
        self.question_text = eval_data.get("task_description", "Question not available")
        self.correct_option = eval_data.get("correct_option", "")

        mc_words = eval_data.get("multiple_choices_word", {})
        mc_images = eval_data.get("multiple_choices_images", {})

        for key in sorted(mc_words.keys()):
            label = mc_words[key]
            img_path = mc_images.get(key, "")
            pixmap = None
            if img_path:
                abs_path = os.path.join(project_root, img_path)
                if os.path.exists(abs_path):
                    pixmap = QPixmap(abs_path)

            self.options.append({
                "key": key,
                "label": label,
                "pixmap": pixmap,
                "is_correct": (key == self.correct_option)
            })

        # Generate sparkles
        self.sparkles = []
        for _ in range(12):
            self.sparkles.append({
                "x": random.uniform(0, 1),
                "y": random.uniform(0, 1),
                "size": random.uniform(3, 7),
                "phase": random.uniform(0, math.pi * 2),
                "hue": random.choice([45, 200, 280, 330, 120])
            })

        self.update()

    def _animate(self):
        self.tick += 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        self._draw_background(p, w, h)
        self._draw_header(p, w, h)
        self._draw_question(p, w, h)
        self._draw_options(p, w, h)
        self._draw_footer(p, w, h)
        self._draw_sparkles(p, w, h)

        p.end()

    def _draw_background(self, p, w, h):
        """Warm pastel gradient background."""
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor(232, 245, 253))    # Light blue
        bg.setColorAt(0.5, QColor(243, 229, 245))   # Soft lavender
        bg.setColorAt(1, QColor(255, 243, 224))      # Warm peach
        p.fillRect(0, 0, w, h, bg)

        # Subtle polka dots
        p.setPen(Qt.NoPen)
        for i in range(30):
            dx = (i * 137 + 50) % w
            dy = (i * 89 + 30) % h
            alpha = 15 + 8 * math.sin(self.tick * 0.03 + i)
            p.setBrush(QColor(150, 100, 200, int(alpha)))
            p.drawEllipse(QPointF(dx, dy), 15, 15)

    def _draw_header(self, p, w, h):
        """Title bar with student name."""
        # Title card background
        card_y = int(h * 0.02)
        card_h = int(h * 0.12)
        card_margin = int(w * 0.05)
        card_rect = QRectF(card_margin, card_y, w - card_margin * 2, card_h)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawRoundedRect(card_rect, 20, 20)

        # Border
        p.setPen(QPen(QColor(100, 149, 237, 120), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(card_rect, 20, 20)

        # Title text
        title_font = QFont("Georgia", 28, QFont.Bold)
        p.setFont(title_font)
        p.setPen(QColor(21, 101, 192))
        pulse = 1.0 + 0.02 * math.sin(self.tick * 0.06)
        emoji_bounce = "👩‍🏫" if int(self.tick * 0.05) % 2 == 0 else "🧑‍🏫"
        p.drawText(card_rect, Qt.AlignCenter,
                   f"{emoji_bounce}  Teacher Time!  {emoji_bounce}")

        # Student name badge (pill shape)
        badge_font = QFont("Georgia", 16, QFont.Bold)
        p.setFont(badge_font)
        badge_text = f"🌟 Student: {self.student_name}"
        badge_w = min(350, int(w * 0.35))
        badge_h = 36
        badge_x = w // 2 - badge_w // 2
        badge_y = card_y + card_h + 8

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 193, 7, 200))
        p.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, badge_h // 2, badge_h // 2)
        p.setPen(QColor(80, 50, 0))
        p.drawText(QRectF(badge_x, badge_y, badge_w, badge_h), Qt.AlignCenter, badge_text)

    def _draw_question(self, p, w, h):
        """Question card with decorative borders."""
        q_y = int(h * 0.20)
        q_h = int(h * 0.10)
        q_margin = int(w * 0.06)
        q_rect = QRectF(q_margin, q_y, w - q_margin * 2, q_h)

        # Card background
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 230))
        p.drawRoundedRect(q_rect, 16, 16)

        # Decorative left accent bar
        accent_rect = QRectF(q_margin, q_y, 6, q_h)
        p.setBrush(QColor(100, 149, 237))
        p.drawRoundedRect(accent_rect, 3, 3)

        # Question text
        q_font = QFont("Georgia", 20, QFont.Bold)
        p.setFont(q_font)
        p.setPen(QColor(30, 30, 80))
        text_rect = QRectF(q_margin + 20, q_y, w - q_margin * 2 - 30, q_h)
        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft | Qt.TextWordWrap,
                   f"❓  {self.question_text}")

    def _draw_options(self, p, w, h):
        """Draw answer option cards in a grid."""
        if not self.options:
            return

        count = len(self.options)
        cols = min(count, 4) if count <= 4 else 2
        rows = math.ceil(count / cols)

        grid_top = int(h * 0.33)
        grid_bottom = int(h * 0.82)
        grid_left = int(w * 0.06)
        grid_right = int(w * 0.94)
        grid_w = grid_right - grid_left
        grid_h = grid_bottom - grid_top

        card_gap = 16
        card_w = (grid_w - (cols - 1) * card_gap) // cols
        card_h = (grid_h - (rows - 1) * card_gap) // rows

        for idx, opt in enumerate(self.options):
            col = idx % cols
            row = idx // cols

            cx = grid_left + col * (card_w + card_gap)
            cy = grid_top + row * (card_h + card_gap)
            card_rect = QRectF(cx, cy, card_w, card_h)

            # Card styling
            if opt["is_correct"]:
                # Correct answer — glowing green
                glow_alpha = int(180 + 40 * math.sin(self.tick * 0.1))
                p.setPen(QPen(QColor(46, 125, 50, glow_alpha), 4))
                p.setBrush(QColor(200, 255, 200, 240))
            else:
                p.setPen(QPen(QColor(180, 180, 200, 100), 2))
                p.setBrush(QColor(255, 255, 255, 200))

            p.drawRoundedRect(card_rect, 18, 18)

            # Option number badge
            badge_size = 32
            badge_x = cx + 8
            badge_y = cy + 8
            if opt["is_correct"]:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(46, 125, 50))
            else:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(100, 149, 237))
            p.drawRoundedRect(int(badge_x), int(badge_y), badge_size, badge_size, badge_size // 2, badge_size // 2)

            badge_font = QFont("Georgia", 14, QFont.Bold)
            p.setFont(badge_font)
            p.setPen(QColor(255, 255, 255))
            option_num = str(idx + 1)
            p.drawText(QRectF(badge_x, badge_y, badge_size, badge_size), Qt.AlignCenter, option_num)

            # Image
            if opt["pixmap"]:
                img_area_top = cy + 44
                img_area_h = card_h - 90
                img_size = min(int(card_w * 0.7), int(img_area_h))
                scaled = opt["pixmap"].scaled(img_size, img_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_x = cx + (card_w - scaled.width()) // 2
                img_y = int(img_area_top + (img_area_h - scaled.height()) // 2)
                p.drawPixmap(int(img_x), int(img_y), scaled)

            # Label text at the bottom of card
            label_font = QFont("Georgia", 13)
            p.setFont(label_font)
            p.setPen(QColor(50, 50, 80))
            label_rect = QRectF(cx + 4, cy + card_h - 36, card_w - 8, 30)
            p.drawText(label_rect, Qt.AlignCenter, opt["label"])

            # Correct answer star marker
            if opt["is_correct"]:
                star_font = QFont("Georgia", 22)
                p.setFont(star_font)
                p.setPen(QColor(255, 193, 7))
                p.drawText(QRectF(cx + card_w - 40, cy + 4, 36, 36), Qt.AlignCenter, "⭐")

                # "CORRECT" tag
                tag_w = 80
                tag_h = 22
                tag_x = cx + card_w - tag_w - 8
                tag_y = cy + card_h - 58
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(46, 125, 50, 220))
                p.drawRoundedRect(int(tag_x), int(tag_y), tag_w, tag_h, 10, 10)
                tag_font = QFont("Georgia", 11, QFont.Bold)
                p.setFont(tag_font)
                p.setPen(QColor(255, 255, 255))
                p.drawText(QRectF(tag_x, tag_y, tag_w, tag_h), Qt.AlignCenter, "✓ CORRECT")

    def _draw_footer(self, p, w, h):
        """Bottom bar with continue prompt and path summary."""
        footer_y = int(h * 0.85)

        # Continue button
        pulse = 0.9 + 0.1 * abs(math.sin(self.tick * 0.07))
        btn_w = int(280 * pulse)
        btn_h = int(52 * pulse)
        btn_x = w // 2 - btn_w // 2
        btn_y = footer_y + 10

        # Shadow
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 30))
        p.drawRoundedRect(btn_x + 2, btn_y + 3, btn_w, btn_h, 15, 15)

        # Button body
        btn_grad = QLinearGradient(btn_x, btn_y, btn_x, btn_y + btn_h)
        btn_grad.setColorAt(0, QColor(25, 118, 210))
        btn_grad.setColorAt(1, QColor(13, 71, 161))
        p.setBrush(btn_grad)
        p.setPen(QPen(QColor(255, 255, 255, 80), 2))
        p.drawRoundedRect(btn_x, btn_y, btn_w, btn_h, 15, 15)

        btn_font = QFont("Georgia", 18, QFont.Bold)
        p.setFont(btn_font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRectF(btn_x, btn_y, btn_w, btn_h), Qt.AlignCenter, "Press  C  to Continue")

        # Path summary (tiny breadcrumb trail)
        if self.path_taken:
            path_y = btn_y + btn_h + 12
            path_font = QFont("Georgia", 10)
            p.setFont(path_font)
            p.setPen(QColor(120, 100, 150, 160))
            trail = " → ".join(self.path_taken[-6:])  # last 6 steps
            p.drawText(QRectF(0, path_y, w, 20), Qt.AlignCenter, f"Learning path: {trail}")

    def _draw_sparkles(self, p, w, h):
        """Decorative animated sparkles."""
        p.setPen(Qt.NoPen)
        for sp in self.sparkles:
            alpha = int(80 + 60 * math.sin(self.tick * 0.06 + sp["phase"]))
            color = QColor.fromHsl(sp["hue"], 200, 200, alpha)
            p.setBrush(color)
            sx = sp["x"] * w
            sy = sp["y"] * h
            size = sp["size"] + 1.5 * math.sin(self.tick * 0.08 + sp["phase"])
            # 4-point star shape
            path = QPainterPath()
            for i in range(4):
                angle = math.radians(i * 90 - 45)
                ox = sx + size * math.cos(angle)
                oy = sy + size * math.sin(angle)
                if i == 0:
                    path.moveTo(ox, oy)
                else:
                    path.lineTo(ox, oy)
                mid_angle = math.radians(i * 90 + 45 - 45)
                mx = sx + size * 0.3 * math.cos(mid_angle)
                my = sy + size * 0.3 * math.sin(mid_angle)
                path.lineTo(mx, my)
            path.closeSubpath()
            p.drawPath(path)


def get_ui():
    """Create the teacher intervention screen with the painted widget."""
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

    input_enabled = False

    # 1. Load task data into the widget
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    task_data = state_manager.get_current_task()
    path = getattr(state_manager, 'current_path', [])

    game_widget.load_task_data(student_name, task_data, path)

    # 2. Robot speech
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

    if action == "CONTINUE":
        input_enabled = False
        voice_manager.stop()
        print("[Teacher Intervention] Teacher pressed CONTINUE. Logging complete cascade and resetting.")

        # Log Result (Complete Cascade Failure -> Teacher Assisted)
        task_data = state_manager.get_current_task()
        task_id = task_data.get("task_id", "unknown") if task_data else "unknown"
        student_id = state_manager.get_current_student() or "unknown"

        # Use the actual path taken if available, otherwise fallback
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

        # Advance Queue Natively
        student_queue = state_manager.get_student_queue()

        if student_queue:
            next_stu = student_queue.pop(0)
            state_manager.set_current_student(next_stu)
            state_manager.set_student_queue(student_queue)

            # Wipe affordance tracking state completely for the next child
            state_manager.current_path = []
            state_manager.set_affordance_level(1)

            try:
                from core.navigator import navigator
                navigator.navigate_to("student_call")
            except Exception as e:
                print(f"Warning: Could not transition back to student_call screen. {e}")
        else:
            try:
                from core.navigator import navigator
                navigator.navigate_to("session_complete")
            except Exception as e:
                print(f"Warning: Could not transition back to session_complete screen. {e}")
