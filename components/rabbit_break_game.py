"""
🐰 Rabbit Break Widget — "Bunny Adventure!"
==============================================
A 3-act animated break screen for Level 2 students who are unresponsive.

Act 1 (Story):    Bunny appears, robot tells the story
Act 2 (Activity): 45-second timer — bunny hops along a dotted path
Act 3 (Return):   Waiting for student to press ENTER

The entire scene is a sunny meadow painted with QPainter.
"""

import os
import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QPainter, QColor, QRadialGradient, QLinearGradient,
    QFont, QPen, QBrush, QPixmap, QPainterPath
)


# ── Asset paths ──
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_IMG_DIR = os.path.join(_BASE_DIR, "assets", "images", "break")
_BUNNY_PATH = os.path.join(_IMG_DIR, "bunny_hop.png")


class Butterfly:
    """A drifting butterfly particle."""
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(h * 0.1, h * 0.6)
        self.size = random.uniform(6, 12)
        self.phase = random.uniform(0, math.pi * 2)
        self.color = QColor.fromHsl(
            random.choice([290, 200, 40, 330, 170]),
            random.randint(180, 255),
            random.randint(160, 220)
        )
        self.w = w
        self.h = h

    def update(self, tick):
        self.x += 0.5 * math.sin(tick * 0.03 + self.phase)
        self.y += 0.3 * math.cos(tick * 0.025 + self.phase)
        if self.x < 0: self.x = self.w
        if self.x > self.w: self.x = 0

    def get_wing_spread(self, tick):
        return 0.5 + 0.5 * abs(math.sin(tick * 0.15 + self.phase))


class Flower:
    """A static flower on the meadow."""
    def __init__(self, x, y, size, color_hue):
        self.x = x
        self.y = y
        self.size = size
        self.color = QColor.fromHsl(color_hue, 220, 180)
        self.center_color = QColor(255, 220, 50)
        self.visible = False
        self.bloom_tick = 0
        self.bloom_progress = 0.0

    def update(self, tick):
        if not self.visible:
            return
        age = tick - self.bloom_tick
        self.bloom_progress = min(1.0, age / 15.0)


class RabbitBreakWidget(QWidget):
    """
    Full-screen animated rabbit break game.

    Phases:
        "story"    → Act 1: Bunny appears, story text
        "activity" → Act 2: Timer countdown, bunny hops along path
        "return"   → Act 3: Waiting for student to press ENTER
    """

    # Signals for the screen to connect to
    activity_complete = Signal()
    halfway_reached = Signal()
    almost_done = Signal()
    return_timeout = Signal()
    return_warning = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)

        # State
        self.phase = "story"
        self.tick = 0

        # Activity timer state
        self.activity_total = 45  # seconds
        self.activity_remaining = 45
        self.activity_running = False
        self._halfway_fired = False
        self._almost_done_fired = False

        # Return timer state
        self.return_total = 60
        self.return_remaining = 60
        self.return_running = False
        self._return_warning_fired = False

        # Bunny hop position along path (0.0 → 1.0)
        self.hop_progress = 0.0

        # Flowers
        self.flowers = []
        self._generate_flowers()

        # Butterflies
        self.butterflies = [Butterfly(900, 700) for _ in range(8)]

        # Load bunny sprite
        self.bunny_pixmap = QPixmap(_BUNNY_PATH) if os.path.exists(_BUNNY_PATH) else None

        # Enter key pulse
        self.enter_pulse = 0.0

        # Animation timer (30 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(33)

        # 1-second countdown timer for activity/return
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._countdown_tick)

    def _generate_flowers(self):
        """Pre-generate flower positions along the ground."""
        self.flowers = []
        for i in range(20):
            x = random.uniform(0.05, 0.95)
            y = random.uniform(0.78, 0.92)
            size = random.uniform(8, 16)
            hue = random.choice([0, 30, 50, 280, 320, 200])
            self.flowers.append(Flower(x, y, size, hue))

    def set_phase(self, phase: str):
        """Transition to a new phase."""
        if phase == self.phase:
            return
        old = self.phase
        self.phase = phase
        print(f"[RabbitBreak] Phase: {old} → {phase}")

        if phase == "activity":
            self.activity_remaining = self.activity_total
            self.activity_running = True
            self.hop_progress = 0.0
            self._halfway_fired = False
            self._almost_done_fired = False
            self.countdown_timer.start(1000)
            # Start blooming flowers progressively
            for flower in self.flowers:
                flower.visible = False

        elif phase == "return":
            self.activity_running = False
            self.countdown_timer.stop()
            self.return_remaining = self.return_total
            self.return_running = True
            self._return_warning_fired = False
            self.countdown_timer.start(1000)
            # All flowers bloom
            for flower in self.flowers:
                if not flower.visible:
                    flower.visible = True
                    flower.bloom_tick = self.tick

        self.update()

    def _countdown_tick(self):
        """Fires every second for activity or return countdown."""
        if self.phase == "activity" and self.activity_running:
            self.activity_remaining -= 1
            elapsed = self.activity_total - self.activity_remaining
            self.hop_progress = min(1.0, elapsed / self.activity_total)

            # Bloom flowers progressively
            bloom_count = int(self.hop_progress * len(self.flowers))
            for i, flower in enumerate(self.flowers):
                if i < bloom_count and not flower.visible:
                    flower.visible = True
                    flower.bloom_tick = self.tick

            # Halfway signal
            if not self._halfway_fired and self.activity_remaining <= self.activity_total // 2:
                self._halfway_fired = True
                self.halfway_reached.emit()

            # Almost done signal
            if not self._almost_done_fired and self.activity_remaining <= 5:
                self._almost_done_fired = True
                self.almost_done.emit()

            # Timer complete
            if self.activity_remaining <= 0:
                self.activity_running = False
                self.countdown_timer.stop()
                self.activity_complete.emit()

        elif self.phase == "return" and self.return_running:
            self.return_remaining -= 1

            # Warning at 15 seconds left
            if not self._return_warning_fired and self.return_remaining <= 15:
                self._return_warning_fired = True
                self.return_warning.emit()

            # Timeout
            if self.return_remaining <= 0:
                self.return_running = False
                self.countdown_timer.stop()
                self.return_timeout.emit()

    def _animate(self):
        """Animation tick at 30 FPS."""
        self.tick += 1
        self.enter_pulse = 0.5 + 0.5 * math.sin(self.tick * 0.08)

        # Update butterflies
        for bf in self.butterflies:
            bf.update(self.tick)

        # Update flowers
        for flower in self.flowers:
            flower.update(self.tick)

        self.update()

    def paintEvent(self, event):
        """Render the current scene."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Always draw the meadow background
        self._draw_meadow(painter, w, h)

        if self.phase == "story":
            self._draw_story(painter, w, h)
        elif self.phase == "activity":
            self._draw_activity(painter, w, h)
        elif self.phase == "return":
            self._draw_return(painter, w, h)

        painter.end()

    # ─────────────────── MEADOW BACKGROUND ───────────────────
    def _draw_meadow(self, p: QPainter, w, h):
        """Sunny meadow with sky, sun, clouds, hills, grass."""
        # Sky gradient
        sky = QLinearGradient(0, 0, 0, h * 0.7)
        sky.setColorAt(0, QColor(135, 206, 250))    # light blue
        sky.setColorAt(0.7, QColor(176, 226, 255))   # softer
        sky.setColorAt(1, QColor(200, 240, 200))      # greenish horizon
        p.fillRect(0, 0, w, h, sky)

        # Sun
        sun_x, sun_y = w * 0.85, h * 0.1
        sun_glow = QRadialGradient(sun_x, sun_y, 120)
        sun_glow.setColorAt(0, QColor(255, 250, 180, 120))
        sun_glow.setColorAt(1, QColor(255, 250, 180, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(sun_glow)
        p.drawEllipse(QPointF(sun_x, sun_y), 120, 120)
        p.setBrush(QColor(255, 230, 80))
        p.drawEllipse(QPointF(sun_x, sun_y), 40, 40)

        # Clouds
        p.setBrush(QColor(255, 255, 255, 180))
        for cx, cy, cw in [(w * 0.2, h * 0.08, 80), (w * 0.5, h * 0.12, 60), (w * 0.7, h * 0.06, 70)]:
            shift = 10 * math.sin(self.tick * 0.01 + cx)
            for dx, dy, r in [(-cw * 0.3, 0, cw * 0.4), (0, -5, cw * 0.5), (cw * 0.3, 0, cw * 0.35)]:
                p.drawEllipse(QPointF(cx + dx + shift, cy + dy), r, r * 0.6)

        # Rolling hills
        hill_path = QPainterPath()
        hill_path.moveTo(0, h)
        hill_path.lineTo(0, h * 0.72)
        for x in range(0, w + 20, 15):
            hy = h * 0.72 + 30 * math.sin(x * 0.006) + 18 * math.cos(x * 0.012)
            hill_path.lineTo(x, hy)
        hill_path.lineTo(w, h)
        hill_path.closeSubpath()

        hill_grad = QLinearGradient(0, h * 0.7, 0, h)
        hill_grad.setColorAt(0, QColor(100, 200, 80))
        hill_grad.setColorAt(0.5, QColor(80, 180, 60))
        hill_grad.setColorAt(1, QColor(60, 140, 45))
        p.fillPath(hill_path, hill_grad)

        # Draw flowers
        for flower in self.flowers:
            if not flower.visible:
                continue
            fx = flower.x * w
            fy = flower.y * h
            s = flower.size * flower.bloom_progress
            if s < 1:
                continue

            # Stem
            p.setPen(QPen(QColor(60, 140, 40), 2))
            p.drawLine(int(fx), int(fy), int(fx), int(fy + s * 1.5))

            # Petals
            p.setPen(Qt.NoPen)
            p.setBrush(flower.color)
            for angle_deg in range(0, 360, 72):
                angle = math.radians(angle_deg)
                px = fx + s * 0.6 * math.cos(angle)
                py = fy + s * 0.6 * math.sin(angle)
                p.drawEllipse(QPointF(px, py), s * 0.4, s * 0.4)

            # Center
            p.setBrush(flower.center_color)
            p.drawEllipse(QPointF(fx, fy), s * 0.3, s * 0.3)

        # Butterflies
        for bf in self.butterflies:
            wing = bf.get_wing_spread(self.tick)
            p.setPen(Qt.NoPen)
            p.setBrush(bf.color)
            ws = bf.size * wing
            p.drawEllipse(QPointF(bf.x - ws * 0.5, bf.y), ws, bf.size * 0.6)
            p.drawEllipse(QPointF(bf.x + ws * 0.5, bf.y), ws, bf.size * 0.6)
            # Body
            p.setBrush(QColor(60, 40, 30))
            p.drawEllipse(QPointF(bf.x, bf.y), 2, bf.size * 0.3)

    # ─────────────────── ACT 1: STORY ───────────────────
    def _draw_story(self, p: QPainter, w, h):
        """Bunny appears with story text."""
        # Draw bunny centered
        if self.bunny_pixmap:
            bunny_h = min(350, int(h * 0.50))
            scaled = self.bunny_pixmap.scaledToHeight(bunny_h, Qt.SmoothTransformation)
            bx = w // 2 - scaled.width() // 2
            by = int(h * 0.35)
            p.drawPixmap(bx, by, scaled)

        # Title
        title_font = QFont("Georgia", 44, QFont.Bold)
        title_y = h * 0.06 + 4 * math.sin(self.tick * 0.04)
        self._draw_fancy_text(p, "🐰 Bunny Adventure! 🐰", title_font,
                              QColor(255, 255, 255), QColor(80, 160, 60, 130),
                              QRectF(0, title_y, w, 70))

        # Subtitle
        sub_font = QFont("Georgia", 22)
        self._draw_fancy_text(p, "Stand up and get ready to hop!", sub_font,
                              QColor(255, 255, 240), QColor(60, 120, 40, 100),
                              QRectF(0, title_y + 75, w, 40))

    # ─────────────────── ACT 2: ACTIVITY ───────────────────
    def _draw_activity(self, p: QPainter, w, h):
        """Timer countdown with bunny hopping along a dotted path."""
        # Dotted path
        path_y = h * 0.60
        path_start_x = w * 0.08
        path_end_x = w * 0.92
        path_len = path_end_x - path_start_x

        # Draw the dotted path
        p.setPen(QPen(QColor(255, 255, 255, 150), 3, Qt.DashLine))
        p.drawLine(int(path_start_x), int(path_y), int(path_end_x), int(path_y))

        # Path markers (start/end)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 100, 100))
        p.drawEllipse(QPointF(path_start_x, path_y), 10, 10)
        p.setBrush(QColor(100, 255, 100))
        p.drawEllipse(QPointF(path_end_x, path_y), 10, 10)

        # Draw bunny hopping along path
        if self.bunny_pixmap:
            bunny_h = min(200, int(h * 0.30))
            scaled = self.bunny_pixmap.scaledToHeight(bunny_h, Qt.SmoothTransformation)
            bunny_x = path_start_x + self.hop_progress * path_len - scaled.width() / 2
            # Hop bounce
            hop_bounce = -25 * abs(math.sin(self.tick * 0.15))
            bunny_y = path_y - scaled.height() + hop_bounce
            p.drawPixmap(int(bunny_x), int(bunny_y), scaled)

        # Footprints behind bunny
        p.setPen(Qt.NoPen)
        footprint_count = int(self.hop_progress * 20)
        for i in range(footprint_count):
            fx = path_start_x + (i / 20.0) * path_len
            alpha = max(50, 200 - i * 8)
            p.setBrush(QColor(180, 140, 100, alpha))
            p.drawEllipse(QPointF(fx - 3, path_y + 5), 4, 6)
            p.drawEllipse(QPointF(fx + 3, path_y + 5), 4, 6)

        # Large circular countdown timer
        self._draw_countdown_circle(p, w // 2, int(h * 0.25), 70,
                                     self.activity_remaining, self.activity_total,
                                     QColor(80, 200, 80))

        # Title
        title_font = QFont("Georgia", 38, QFont.Bold)
        self._draw_fancy_text(p, "🐰 Hop Hop Hop!", title_font,
                              QColor(255, 255, 255), QColor(80, 160, 60, 130),
                              QRectF(0, h * 0.02, w, 55))

        # Bottom encouraging text
        if self.activity_remaining > self.activity_total // 2:
            msg = "Jump like a bunny! Go go go! 🏃"
        elif self.activity_remaining > 5:
            msg = "Great hopping! Keep going! 💪"
        else:
            msg = "Almost done! Hop back to your seat! 🎉"

        bottom_font = QFont("Georgia", 22, QFont.Bold)
        self._draw_fancy_text(p, msg, bottom_font,
                              QColor(255, 255, 240), QColor(60, 120, 40, 100),
                              QRectF(0, h * 0.88, w, 40))

    # ─────────────────── ACT 3: RETURN ───────────────────
    def _draw_return(self, p: QPainter, w, h):
        """Waiting for student to press ENTER."""
        # Draw bunny (finished journey, happy at the end)
        if self.bunny_pixmap:
            bunny_h = min(300, int(h * 0.42))
            scaled = self.bunny_pixmap.scaledToHeight(bunny_h, Qt.SmoothTransformation)
            bx = w // 2 - scaled.width() // 2
            by = int(h * 0.33)
            p.drawPixmap(bx, by, scaled)

        # Title
        title_font = QFont("Georgia", 42, QFont.Bold)
        title_y = h * 0.04 + 3 * math.sin(self.tick * 0.04)
        self._draw_fancy_text(p, "🎉 Welcome Back! 🎉", title_font,
                              QColor(255, 255, 255), QColor(80, 160, 60, 130),
                              QRectF(0, title_y, w, 65))

        # Pulsing ENTER button
        pulse_scale = 0.9 + 0.1 * self.enter_pulse
        btn_w = int(320 * pulse_scale)
        btn_h = int(70 * pulse_scale)
        btn_x = w // 2 - btn_w // 2
        btn_y = int(h * 0.80)

        # Button shadow
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawRoundedRect(btn_x + 3, btn_y + 4, btn_w, btn_h, 20, 20)

        # Button body
        btn_grad = QLinearGradient(btn_x, btn_y, btn_x, btn_y + btn_h)
        btn_grad.setColorAt(0, QColor(76, 175, 80))
        btn_grad.setColorAt(1, QColor(56, 142, 60))
        p.setBrush(btn_grad)
        p.setPen(QPen(QColor(255, 255, 255, 100), 2))
        p.drawRoundedRect(btn_x, btn_y, btn_w, btn_h, 20, 20)

        # Button text
        btn_font = QFont("Georgia", 26, QFont.Bold)
        p.setFont(btn_font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRectF(btn_x, btn_y, btn_w, btn_h), Qt.AlignCenter, "🎤 Say 'OKAY'")

        # Countdown (subtle)
        if self.return_remaining <= 15:
            warn_font = QFont("Georgia", 16)
            p.setFont(warn_font)
            p.setPen(QColor(255, 100, 80, 200))
            p.drawText(QRectF(0, h * 0.92, w, 30), Qt.AlignCenter,
                       f"⏰ Hurry! {self.return_remaining}s remaining...")

    # ─────────────────── HELPERS ───────────────────
    def _draw_countdown_circle(self, p: QPainter, cx, cy, radius, remaining, total, color):
        """Large circular countdown with seconds displayed."""
        progress = remaining / total if total > 0 else 0

        # Background ring
        p.setPen(QPen(QColor(255, 255, 255, 50), 8))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        # Progress arc
        if progress > 0:
            p.setPen(QPen(color, 10, Qt.SolidLine, Qt.RoundCap))
            span = int(-progress * 360 * 16)
            p.drawArc(QRectF(cx - radius, cy - radius, radius * 2, radius * 2),
                      90 * 16, span)

        # Center text (seconds)
        sec_font = QFont("Georgia", 32, QFont.Bold)
        p.setFont(sec_font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRectF(cx - radius, cy - 18, radius * 2, 40),
                   Qt.AlignCenter, f"{remaining}s")

    def _draw_fancy_text(self, p: QPainter, text, font, color, glow_color, rect):
        """Draw text with a soft glow halo behind it."""
        p.setFont(font)
        p.setPen(glow_color)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
            p.drawText(rect.adjusted(dx, dy, dx, dy), Qt.AlignCenter, text)
        p.setPen(QColor(0, 0, 0, 60))
        p.drawText(rect.adjusted(2, 3, 2, 3), Qt.AlignCenter, text)
        p.setPen(color)
        p.drawText(rect, Qt.AlignCenter, text)

    def stop_all(self):
        """Stop all timers — cleanup for screen exit."""
        self.activity_running = False
        self.return_running = False
        self.countdown_timer.stop()

    def reset(self):
        """Reset all state for a new break session."""
        self.stop_all()
        self.phase = "story"
        self.tick = 0
        self.hop_progress = 0.0
        self.activity_remaining = self.activity_total
        self.return_remaining = self.return_total
        self._halfway_fired = False
        self._almost_done_fired = False
        self._return_warning_fired = False
        self._generate_flowers()
        self.update()
