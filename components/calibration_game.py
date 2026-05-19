"""
🎮 Calibration Game Widget — "Jinglu's Magical Eyes"
=====================================================
A 3-act animated mini-game that replaces the boring calibration screen.

Act 1 (Eyes OPEN):  "Owl Eyes!"     — Stars fill a night sky
Act 2 (Eyes CLOSED): "Sleeping Bunny!" — Moon rises over meadow  
Act 3 (DONE):        "Super Power!"  — Confetti celebration

Children believe they're playing a game — they never know they're being calibrated.
"""

import os
import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QRadialGradient, QLinearGradient,
    QFont, QPen, QBrush, QPixmap, QPainterPath
)


# ── Asset paths ──
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_IMG_DIR = os.path.join(_BASE_DIR, "assets", "images", "calibration")
_OWL_PATH = os.path.join(_IMG_DIR, "owl.png")
_BUNNY_PATH = os.path.join(_IMG_DIR, "bunny.png")
_CELEBRATION_PATH = os.path.join(_IMG_DIR, "celebration.png")


class Star:
    """A single twinkling star particle."""
    def __init__(self, x, y, size, twinkle_speed):
        self.x = x
        self.y = y
        self.size = size
        self.twinkle_speed = twinkle_speed
        self.phase = random.uniform(0, math.pi * 2)
        self.rotation = random.uniform(0, 360)  # random tilt
        self.visible = False
        self.birth_tick = 0
        self.alpha = 0.0

    def update(self, tick):
        if not self.visible:
            return
        age = tick - self.birth_tick
        # Fade in over 10 ticks
        self.alpha = min(1.0, age / 10.0)

    def get_brightness(self, tick):
        if not self.visible:
            return 0
        twinkle = 0.6 + 0.4 * math.sin(tick * self.twinkle_speed + self.phase)
        return self.alpha * twinkle


class Firefly:
    """A drifting firefly particle for the sleeping scene."""
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(h * 0.3, h * 0.9)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.2, 0.2)
        self.size = random.uniform(2, 5)
        self.phase = random.uniform(0, math.pi * 2)
        self.w = w
        self.h = h

    def update(self, tick):
        self.x += self.vx + 0.2 * math.sin(tick * 0.03 + self.phase)
        self.y += self.vy + 0.1 * math.cos(tick * 0.02 + self.phase)
        # Wrap around
        if self.x < 0: self.x = self.w
        if self.x > self.w: self.x = 0
        if self.y < 0: self.y = self.h
        if self.y > self.h: self.y = 0

    def get_glow(self, tick):
        return 0.4 + 0.6 * abs(math.sin(tick * 0.05 + self.phase))


class ConfettiPiece:
    """A falling confetti piece for the celebration."""
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(-h, 0)
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(2, 6)
        self.size = random.uniform(4, 10)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)
        self.color = QColor.fromHsl(
            random.randint(0, 359),
            random.randint(180, 255),
            random.randint(140, 220)
        )

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.rot_speed
        self.vx += random.uniform(-0.1, 0.1)


class CalibrationGameWidget(QWidget):
    """
    Full-screen animated calibration game.
    
    Phases:
        "init"   → Intro screen ("Get ready for magic!")
        "open"   → Act 1: Owl Eyes (stars filling)
        "closed" → Act 2: Sleeping Bunny (moon rising)
        "done"   → Act 3: Celebration
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)

        # State
        self.phase = "init"  # init, open, closed, done
        self.tick = 0
        self.progress = 0.0  # 0.0 → 1.0 within current phase
        self.calibration_total = 200

        # Stars for Act 1
        self.stars = []
        self.max_stars = 20
        self._generate_stars()

        # Fireflies for Act 2
        self.fireflies = [Firefly(900, 700) for _ in range(25)]

        # Confetti for Act 3
        self.confetti = []
        self.celebration_started = False

        # Load character sprites
        self.owl_pixmap = QPixmap(_OWL_PATH) if os.path.exists(_OWL_PATH) else None
        self.bunny_pixmap = QPixmap(_BUNNY_PATH) if os.path.exists(_BUNNY_PATH) else None
        self.celebration_pixmap = QPixmap(_CELEBRATION_PATH) if os.path.exists(_CELEBRATION_PATH) else None
        
        self.cached_owl = None
        self.cached_bunny = None
        self.cached_celebration = None
        self.last_h = 0

    def _get_scaled_pixmap(self, original, target_h):
        if original is None: return None
        if self.last_h == target_h and self.cached_owl and original == self.owl_pixmap: return self.cached_owl
        if self.last_h == target_h and self.cached_bunny and original == self.bunny_pixmap: return self.cached_bunny
        if self.last_h == target_h and self.cached_celebration and original == self.celebration_pixmap: return self.cached_celebration
        
        scaled = original.scaledToHeight(target_h, Qt.SmoothTransformation)
        if original == self.owl_pixmap: self.cached_owl = scaled
        elif original == self.bunny_pixmap: self.cached_bunny = scaled
        elif original == self.celebration_pixmap: self.cached_celebration = scaled
        self.last_h = target_h
        return scaled


        # Animation timer (30 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(33)


    def _generate_stars(self):
        """Pre-generate star positions (left 70% to avoid owl on right)."""
        self.stars = []
        for _ in range(self.max_stars):
            x = random.uniform(0.03, 0.65)
            y = random.uniform(0.05, 0.60)
            size = random.uniform(4.0, 10.0)  # bigger since they're proper star shapes
            speed = random.uniform(0.05, 0.15)
            self.stars.append(Star(x, y, size, speed))

    def set_phase(self, phase: str):
        """Transition to a new phase."""
        if phase == self.phase:
            return
        old = self.phase
        self.phase = phase
        self.progress = 0.0
        print(f"[CalibrationGame] Phase: {old} → {phase}")

        if phase == "done" and not self.celebration_started:
            self.celebration_started = True
            w, h = self.width(), self.height()
            self.confetti = [ConfettiPiece(w, h) for _ in range(120)]

        self.update()

    def update_progress(self, current_frame: int, total_frames: int):
        """Update calibration progress (0.0 → 1.0)."""
        self.calibration_total = total_frames
        if total_frames > 0:
            half = total_frames // 2
            if self.phase == "open":
                self.progress = min(1.0, current_frame / half)
            elif self.phase == "closed":
                self.progress = min(1.0, (current_frame - half) / half)

            # Reveal stars progressively
            if self.phase == "open":
                visible_count = int(self.progress * self.max_stars)
                for i, star in enumerate(self.stars):
                    if i < visible_count and not star.visible:
                        star.visible = True
                        star.birth_tick = self.tick

    def _animate(self):
        """Animation tick."""
        if not self.isVisible():
            return

        self.tick += 1

        # Update stars
        for star in self.stars:
            star.update(self.tick)

        # Update fireflies
        if self.phase == "closed":
            for ff in self.fireflies:
                ff.update(self.tick)

        # Update confetti
        if self.phase == "done":
            for piece in self.confetti:
                piece.update()

        self.update()

    def paintEvent(self, event):
        """Render the current scene."""
        if not self.isVisible():
            return
            
        painter = QPainter(self)
        if not painter.isActive():
            return
            
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()

            if self.phase == "init":
                self._draw_intro(painter, w, h)
            elif self.phase == "open":
                self._draw_owl_scene(painter, w, h)
            elif self.phase == "closed":
                self._draw_bunny_scene(painter, w, h)
            elif self.phase == "done":
                self._draw_celebration(painter, w, h)
        except Exception as e:
            print(f"[CalibrationGame] Paint error: {e}")
        finally:
            painter.end()

    # ─────────────────── INTRO SCENE ───────────────────
    def _draw_intro(self, p: QPainter, w, h):
        """Sparkly intro screen."""
        # Deep blue gradient background
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(15, 10, 50))
        grad.setColorAt(1, QColor(30, 20, 80))
        p.fillRect(0, 0, w, h, grad)

        # Animated shimmer dots
        for i in range(30):
            x = (i * 137 + self.tick * 0.5) % w
            y = (i * 89 + self.tick * 0.3) % h
            alpha = int(80 + 60 * math.sin(self.tick * 0.08 + i))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(200, 200, 255, alpha))
            p.drawEllipse(QPointF(x, y), 2, 2)

        # Title text with glow
        title_font = QFont("Georgia", 52, QFont.Bold)
        title_y = h * 0.30 + 8 * math.sin(self.tick * 0.04)
        self._draw_fancy_text(p, "✨ Get Ready for Magic! ✨", title_font,
                              QColor(255, 255, 255), QColor(180, 140, 255, 120),
                              QRectF(0, title_y, w, 80))

        # Subtitle
        sub_font = QFont("Georgia", 26)
        self._draw_fancy_text(p, "Look at Jinglu's camera...", sub_font,
                              QColor(200, 190, 255), QColor(100, 80, 180, 80),
                              QRectF(0, title_y + 85, w, 50))

        # Draw owl preview peeking from the right
        if self.owl_pixmap:
            owl_h = int(h * 0.55)
            scaled = self._get_scaled_pixmap(self.owl_pixmap, owl_h)
            owl_x = w - int(scaled.width() * 0.75)
            owl_y = int(h * 0.42)
            p.drawPixmap(owl_x, owl_y, scaled)

    # ─────────────────── OWL SCENE (Eyes Open) ───────────────────
    def _draw_owl_scene(self, p: QPainter, w, h):
        """Act 1: Night sky with stars appearing + owl character."""
        # Dark night sky gradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(5, 5, 30))
        grad.setColorAt(0.5, QColor(15, 15, 60))
        grad.setColorAt(1, QColor(20, 30, 70))
        p.fillRect(0, 0, w, h, grad)

        # Draw stars (proper 5-pointed star shapes)
        for star in self.stars:
            if not star.visible:
                continue
            brightness = star.get_brightness(self.tick)
            sx = star.x * w
            sy = star.y * h
            alpha = int(255 * brightness)
            size = star.size * (0.8 + 0.4 * brightness)

            # Star glow (soft circle behind the star)
            glow_color = QColor(220, 230, 255, int(alpha * 0.2))
            p.setPen(Qt.NoPen)
            p.setBrush(glow_color)
            p.drawEllipse(QPointF(sx, sy), size * 2.5, size * 2.5)

            # Star shape
            core_color = QColor(255, 255, 210, alpha)
            p.setBrush(core_color)
            p.setPen(Qt.NoPen)
            star_path = self._make_star_path(sx, sy, size, size * 0.4, 5, star.rotation)
            p.drawPath(star_path)

        # Ground silhouette (gentle hills)
        ground_path = QPainterPath()
        ground_path.moveTo(0, h)
        ground_path.lineTo(0, h * 0.82)
        for x in range(0, w + 20, 20):
            gy = h * 0.82 + 25 * math.sin(x * 0.008) + 15 * math.cos(x * 0.015)
            ground_path.lineTo(x, gy)
        ground_path.lineTo(w, h)
        ground_path.closeSubpath()

        ground_grad = QLinearGradient(0, h * 0.8, 0, h)
        ground_grad.setColorAt(0, QColor(10, 25, 15))
        ground_grad.setColorAt(1, QColor(5, 15, 8))
        p.fillPath(ground_path, ground_grad)

        # Draw owl character — anchored to right side, branch extends off-screen
        if self.owl_pixmap:
            owl_h = min(450, int(h * 0.7))
            scaled = self._get_scaled_pixmap(self.owl_pixmap, owl_h)
            # Position so the right part of the branch goes off the window edge
            owl_x = w - int(scaled.width() * 0.72)
            owl_y = int(h * 0.22)
            p.drawPixmap(owl_x, owl_y, scaled)

        # Constellation progress arc (centered in left area, bigger)
        self._draw_progress_arc(p, int(w * 0.3), int(h * 0.5), 65, self.progress, QColor(255, 220, 100))

        # Phase label
        label_font = QFont("Georgia", 36, QFont.Bold)
        label_y = h * 0.08 + 3 * math.sin(self.tick * 0.05)
        self._draw_fancy_text(p, "🦉 Owl Eyes! Keep watching!", label_font,
                              QColor(255, 245, 200), QColor(200, 160, 50, 100),
                              QRectF(0, label_y, w * 0.7, 60))

        # Star count
        visible = sum(1 for s in self.stars if s.visible)
        count_font = QFont("Georgia", 20)
        self._draw_fancy_text(p, f"⭐ {visible} / {self.max_stars} stars discovered!", count_font,
                              QColor(200, 215, 255, 220), QColor(100, 120, 200, 60),
                              QRectF(0, h - 55, w * 0.7, 40))

    # ─────────────────── BUNNY SCENE (Eyes Closed) ───────────────────
    def _draw_bunny_scene(self, p: QPainter, w, h):
        """Act 2: Moonlit meadow with sleeping bunny."""
        # Deep purple night gradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(20, 10, 50))
        grad.setColorAt(0.4, QColor(35, 20, 70))
        grad.setColorAt(1, QColor(15, 25, 40))
        p.fillRect(0, 0, w, h, grad)

        # Moon (rises based on progress)
        moon_x = w * 0.78
        moon_start_y = h * 0.6
        moon_end_y = h * 0.12
        moon_y = moon_start_y + (moon_end_y - moon_start_y) * self.progress
        moon_radius = 40

        # Moon glow
        moon_glow = QRadialGradient(moon_x, moon_y, moon_radius * 4)
        moon_glow.setColorAt(0, QColor(255, 250, 200, 50))
        moon_glow.setColorAt(1, QColor(255, 250, 200, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(moon_glow)
        p.drawEllipse(QPointF(moon_x, moon_y), moon_radius * 4, moon_radius * 4)

        # Moon body
        p.setBrush(QColor(255, 250, 220))
        p.drawEllipse(QPointF(moon_x, moon_y), moon_radius, moon_radius)

        # Dim stars in background (proper star shapes)
        for i in range(15):
            sx = (i * 163) % w
            sy = (i * 97) % int(h * 0.5)
            alpha = int(50 + 40 * math.sin(self.tick * 0.06 + i * 0.7))
            size = 3.0 + (i % 3)
            star_color = QColor(220, 220, 255, alpha)
            p.setPen(Qt.NoPen)
            p.setBrush(star_color)
            rotation = i * 37  # deterministic rotation per star
            star_path = self._make_star_path(sx, sy, size, size * 0.4, 5, rotation)
            p.drawPath(star_path)

        # Fireflies
        for ff in self.fireflies:
            glow = ff.get_glow(self.tick)
            alpha = int(200 * glow)
            # Outer glow
            p.setBrush(QColor(200, 255, 150, int(alpha * 0.3)))
            p.drawEllipse(QPointF(ff.x, ff.y), ff.size * 3, ff.size * 3)
            # Core
            p.setBrush(QColor(230, 255, 180, alpha))
            p.drawEllipse(QPointF(ff.x, ff.y), ff.size, ff.size)

        # Meadow ground
        ground_path = QPainterPath()
        ground_path.moveTo(0, h)
        ground_path.lineTo(0, h * 0.75)
        for x in range(0, w + 20, 20):
            gy = h * 0.75 + 20 * math.sin(x * 0.01) + 10 * math.cos(x * 0.02)
            ground_path.lineTo(x, gy)
        ground_path.lineTo(w, h)
        ground_path.closeSubpath()

        meadow_grad = QLinearGradient(0, h * 0.73, 0, h)
        meadow_grad.setColorAt(0, QColor(25, 50, 30))
        meadow_grad.setColorAt(1, QColor(15, 35, 20))
        p.fillPath(ground_path, meadow_grad)

        # Draw bunny character (static, no wiggle)
        if self.bunny_pixmap:
            bunny_h = min(380, int(h * 0.50))
            scaled = self._get_scaled_pixmap(self.bunny_pixmap, bunny_h)
            bunny_x = w // 2 - scaled.width() // 2
            bunny_y = int(h * 0.46)
            p.drawPixmap(bunny_x, bunny_y, scaled)

        # Moon progress arc (near the moon)
        self._draw_progress_arc(p, w - 80, 70, 45, self.progress, QColor(200, 180, 255))

        # Phase label
        label_font = QFont("Georgia", 36, QFont.Bold)
        label_y = h * 0.08 + 3 * math.sin(self.tick * 0.04)
        self._draw_fancy_text(p, "🐰 Shh... Sleeping Bunny!", label_font,
                              QColor(230, 210, 255), QColor(140, 100, 200, 100),
                              QRectF(0, label_y, w, 60))

        # Moon progress text
        count_font = QFont("Georgia", 20)
        self._draw_fancy_text(p, f"🌙 Moon rising... {int(self.progress * 100)}%", count_font,
                              QColor(220, 200, 255, 220), QColor(100, 80, 180, 60),
                              QRectF(0, h - 55, w, 40))

    # ─────────────────── CELEBRATION (Done) ───────────────────
    def _draw_celebration(self, p: QPainter, w, h):
        """Act 3: Confetti celebration!"""
        # Vibrant gradient background
        t = self.tick * 0.02
        hue_shift = int(30 * math.sin(t))
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor.fromHsl((260 + hue_shift) % 360, 200, 80))
        grad.setColorAt(0.5, QColor.fromHsl((280 + hue_shift) % 360, 180, 60))
        grad.setColorAt(1, QColor.fromHsl((240 + hue_shift) % 360, 200, 50))
        p.fillRect(0, 0, w, h, grad)

        # Draw confetti
        for piece in self.confetti:
            if piece.y > h + 20:
                continue
            p.save()
            p.translate(piece.x, piece.y)
            p.rotate(piece.rotation)
            p.setPen(Qt.NoPen)
            p.setBrush(piece.color)
            p.drawRect(int(-piece.size / 2), int(-piece.size / 2),
                       int(piece.size), int(piece.size * 0.6))
            p.restore()

        # Radiating glow
        center_glow = QRadialGradient(w / 2, h * 0.4, 200)
        center_glow.setColorAt(0, QColor(255, 255, 200, 80))
        center_glow.setColorAt(1, QColor(255, 255, 200, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(center_glow)
        p.drawEllipse(QPointF(w / 2, h * 0.4), 250, 250)

        # "SUPER POWER!" text with pulsing
        pulse = 1.0 + 0.05 * math.sin(self.tick * 0.1)
        title_size = int(58 * pulse)
        title_font = QFont("Georgia", title_size, QFont.Bold)

        # Text shadow
        p.setFont(title_font)
        p.setPen(QColor(0, 0, 0, 100))
        p.drawText(QRectF(4, h * 0.16 + 4, w, 80), Qt.AlignCenter, "⚡ SUPER POWER! ⚡")

        # Text
        p.setPen(QColor(255, 255, 100))
        p.drawText(QRectF(0, h * 0.16, w, 80), Qt.AlignCenter, "⚡ SUPER POWER! ⚡")

        # Subtitle
        sub_font = QFont("Georgia", 30, QFont.Bold)
        self._draw_fancy_text(p, "Your magical eyes are charged!", sub_font,
                              QColor(255, 255, 255), QColor(200, 150, 255, 80),
                              QRectF(0, h * 0.30, w, 50))

        # Draw celebration image (single combined owl+bunny, centered, static)
        if self.celebration_pixmap:
            cel_h = min(350, int(h * 0.50))
            scaled = self._get_scaled_pixmap(self.celebration_pixmap, cel_h)
            p.drawPixmap(int(w / 2 - scaled.width() / 2),
                         int(h * 0.42), scaled)

    # ─────────────────── HELPERS ───────────────────
    def _draw_progress_arc(self, p: QPainter, cx, cy, radius, progress, color: QColor):
        """Draw a circular progress indicator."""
        # Background ring
        p.setPen(QPen(QColor(255, 255, 255, 30), 4))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        # Progress arc
        if progress > 0:
            p.setPen(QPen(color, 5, Qt.SolidLine, Qt.RoundCap))
            span = int(-progress * 360 * 16)  # Qt uses 1/16th of a degree
            p.drawArc(QRectF(cx - radius, cy - radius, radius * 2, radius * 2),
                      90 * 16, span)

        # Percentage text
        pct_font = QFont("Arial", 11, QFont.Bold)
        p.setFont(pct_font)
        p.setPen(color)
        p.drawText(QRectF(cx - radius, cy - 9, radius * 2, 22),
                   Qt.AlignCenter, f"{int(progress * 100)}%")

    def _draw_fancy_text(self, p: QPainter, text, font, color, glow_color, rect):
        """Draw text with a soft glow halo behind it for a magical look."""
        p.setFont(font)
        # Glow layers (draw the text multiple times offset in each direction)
        p.setPen(glow_color)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
            p.drawText(rect.adjusted(dx, dy, dx, dy), Qt.AlignCenter, text)
        # Shadow
        p.setPen(QColor(0, 0, 0, 60))
        p.drawText(rect.adjusted(2, 3, 2, 3), Qt.AlignCenter, text)
        # Main text
        p.setPen(color)
        p.drawText(rect, Qt.AlignCenter, text)

    @staticmethod
    def _make_star_path(cx, cy, outer_r, inner_r, points, rotation_deg=0):
        """Create a 5-pointed star QPainterPath."""
        path = QPainterPath()
        angle_step = math.pi / points  # half-step between outer and inner
        start_angle = math.radians(rotation_deg) - math.pi / 2  # top-pointing by default

        for i in range(points * 2):
            r = outer_r if i % 2 == 0 else inner_r
            angle = start_angle + i * angle_step
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        return path

    def reset(self):
        """Reset all state for a new calibration session."""
        self.phase = "init"
        self.tick = 0
        self.progress = 0.0
        self.celebration_started = False
        self.confetti = []
        self._generate_stars()
        for ff in self.fireflies:
            ff.__init__(self.width() or 900, self.height() or 700)
        self.update()
