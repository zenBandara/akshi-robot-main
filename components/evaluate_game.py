"""
🌿 Evaluate Game Widget — "Jinglu's Enchanted Forest"
=====================================================
A QPainter-based game world for evaluation screens.

Scene: Sunny meadow with sky, sun, clouds, rolling hills, flowers, butterflies.
       Wise owl on a branch asks the question via speech bubble.
       Answer options sit on signpost cards growing from the grass.

Supports L1 (4 cards), L2 (2 cards), L3 (2 cards, warm tones).
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
_IMG_DIR = os.path.join(_BASE_DIR, "assets", "images", "evaluate")
_OWL_PATH = os.path.join(_IMG_DIR, "owl_thinking.png")


class _Butterfly:
    """A drifting butterfly particle."""
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(h * 0.05, h * 0.45)
        self.size = random.uniform(5, 10)
        self.phase = random.uniform(0, math.pi * 2)
        self.color = QColor.fromHsl(
            random.choice([290, 200, 40, 330, 170]),
            random.randint(180, 255), random.randint(160, 220)
        )
        self.w = w

    def update(self, tick):
        self.x += 0.4 * math.sin(tick * 0.025 + self.phase)
        self.y += 0.25 * math.cos(tick * 0.02 + self.phase)
        if self.x < -10: self.x = self.w + 10
        if self.x > self.w + 10: self.x = -10

    def get_wing_spread(self, tick):
        return 0.5 + 0.5 * abs(math.sin(tick * 0.14 + self.phase))


class _Flower:
    """A static meadow flower."""
    def __init__(self, x, y, size, hue):
        self.x = x
        self.y = y
        self.size = size
        self.color = QColor.fromHsl(hue, 220, 180)
        self.center_color = QColor(255, 220, 50)


class _Star:
    """A twinkling, drifting star for the space theme."""
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.size = random.uniform(1, 3)
        self.speed = random.uniform(0.05, 0.2)
        self.twinkle_speed = random.uniform(0.02, 0.08)
        self.phase = random.uniform(0, math.pi * 2)
        self.color = QColor(255, 255, random.randint(200, 255))
        self.opacity = 255
        self.w, self.h = w, h

    def update(self, tick):
        self.x -= self.speed
        if self.x < 0:
            self.x = self.w
            self.y = random.uniform(0, self.h)
        self.opacity = 150 + 100 * math.sin(tick * self.twinkle_speed + self.phase)


class _Nebula:
    """A soft, pulsing nebula cloud."""
    def __init__(self, w, h):
        self.x = random.uniform(0.2, 0.8) * w
        self.y = random.uniform(0.2, 0.8) * h
        self.radius = random.uniform(150, 400)
        self.color = QColor.fromHsl(random.choice([260, 200, 300, 220]), 200, 50, 40)
        self.pulse_phase = random.uniform(0, math.pi * 2)
        self.pulse_speed = random.uniform(0.005, 0.015)

    def get_current_state(self, tick):
        pulse = 0.8 + 0.2 * math.sin(tick * self.pulse_speed + self.pulse_phase)
        return self.x, self.y, self.radius * pulse, self.color


class EvaluateGameWidget(QWidget):
    """
    Full-screen enchanted forest evaluation scene.

    Usage:
        widget.set_question("Which arrow points right?",
                            [{"key":"op1","label":"Left","pixmap":px}, ...],
                            level=1)
        widget.highlight_answer("op2", correct=True)
    """

    option_selected = Signal(str)   # emitted when a card is "pressed"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.tick = 0

        # Data
        self.question_text = ""
        self.options = []  # list of {key, label, pixmap, is_correct}
        self.level = 1
        self.student_name = ""
        self.highlighted_key = None
        self.highlight_correct = None  # True=green, False=red, 'present'=blue, None=none
        self.highlight_tick = 0
        self.wrong_keys = set()  # Keys permanently marked as wrong
        self.focus_mode = False  # If True, dim everything except the board/card

        # Timer progress (0.0 → 1.0, decreasing)
        self.timer_progress = 1.0

        # Scene elements
        self.flowers = []
        self.butterflies = []
        self.stars = []
        self.nebulae = []
        self._generate_scene(900, 700)

        # Owl sprite
        self.owl_pixmap = QPixmap(_OWL_PATH) if os.path.exists(_OWL_PATH) else None

        # Level 3 Gamified Background
        self.l3_bg_path = os.path.join(_IMG_DIR, "level3eval.png")
        if not os.path.exists(self.l3_bg_path):
            self.l3_bg_path = os.path.join(_IMG_DIR, "eval3background.png")
        if not os.path.exists(self.l3_bg_path):
            self.l3_bg_path = os.path.join(_IMG_DIR, "level3_bg.jpg")
        if not os.path.exists(self.l3_bg_path):
            self.l3_bg_path = os.path.join(_IMG_DIR, "level3_bg.png")
        self.l3_bg_pixmap = QPixmap(self.l3_bg_path) if os.path.exists(self.l3_bg_path) else None

        # Animation (25 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(40)

    def _generate_scene(self, w, h):
        """Pre-generate flowers, butterflies, and space elements."""
        self.flowers = []
        for _ in range(14):
            fx = random.uniform(0.03, 0.97)
            fy = random.uniform(0.80, 0.93)
            fs = random.uniform(6, 13)
            fh = random.choice([0, 30, 50, 280, 320, 200])
            self.flowers.append(_Flower(fx, fy, fs, fh))
        self.butterflies = [_Butterfly(w, h) for _ in range(5)]
        
        # Space elements
        self.stars = [_Star(w, h) for _ in range(80)]
        self.nebulae = [_Nebula(w, h) for _ in range(3)]

    def set_question(self, text, options, level=1, student_name=""):
        """
        Set the evaluation question and answer options.

        options: list of dicts with keys: key, label, pixmap (QPixmap or None)
        """
        self.question_text = text
        self.options = options
        self.level = level
        self.student_name = student_name
        self.highlighted_key = None
        self.highlight_correct = None
        self.wrong_keys.clear()
        self.timer_progress = 1.0
        self.update()

    def set_timer_progress(self, progress):
        """Set timer progress (1.0 = full, 0.0 = expired)."""
        self.timer_progress = max(0.0, min(1.0, progress))
        self.update()

    def highlight_answer(self, key, correct=True):
        """Flash an answer card green (correct), red (wrong), or blue ('present')."""
        self.highlighted_key = key
        self.highlight_correct = correct
        self.highlight_tick = self.tick
        self.update()

    def mark_wrong(self, key):
        """Permanently mark a card as wrong (red)."""
        self.wrong_keys.add(key)
        self.update()

    def clear_highlight(self):
        self.highlighted_key = None
        self.highlight_correct = None
        self.focus_mode = False
        self.update()

    def set_focus_mode(self, focus):
        """Enable/disable background dimming for better focus."""
        self.focus_mode = focus
        self.update()

    def _animate(self):
        self.tick += 1
        for bf in self.butterflies:
            bf.update(self.tick)
        for star in self.stars:
            star.update(self.tick)
        self.update()

    def _get_hill_y(self, x, w, h):
        """Get the hill surface Y at a given pixel X."""
        base_y = h * 0.72
        return base_y + 25 * math.sin(x * 0.005) + 15 * math.cos(x * 0.011)

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            p.setRenderHint(QPainter.TextAntialiasing)
            w, h = self.width(), self.height()

            if self.level >= 3:
                # Level 3: Underwater Gamified Theme (eval3background.png)
                if self.l3_bg_pixmap and not self.l3_bg_pixmap.isNull():
                    p.drawPixmap(0, 0, w, h, self.l3_bg_pixmap.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
                else:
                    # 1. Base Dark Void
                    grad = QLinearGradient(0, 0, 0, h)
                    grad.setColorAt(0, QColor(5, 5, 20))
                    grad.setColorAt(1, QColor(0, 0, 5))
                    p.fillRect(0, 0, w, h, grad)

                    # 2. Pulsing Nebulae
                    for neb in self.nebulae:
                        nx, ny, nr, ncolor = neb.get_current_state(self.tick)
                        neb_grad = QRadialGradient(nx, ny, max(1.0, nr))
                        neb_grad.setColorAt(0, ncolor)
                        neb_grad.setColorAt(1, QColor(0, 0, 0, 0))
                        p.setPen(Qt.NoPen)
                        p.setBrush(neb_grad)
                        p.drawEllipse(QPointF(nx, ny), nr, nr)

                    # 3. Twinkling Stars
                    p.setPen(Qt.NoPen)
                    for star in self.stars:
                        star_color = QColor(star.color)
                        star_color.setAlpha(int(star.opacity))
                        p.setBrush(star_color)
                        p.drawEllipse(QPointF(star.x, star.y), star.size, star.size)
                
                # Dim the background if in focus mode
                if self.focus_mode:
                    p.setPen(Qt.NoPen)
                    p.setBrush(QColor(0, 0, 0, 140))
                    p.drawRect(0, 0, w, h)

                # Draw only focused components
                self._draw_owl_and_bubble(p, w, h)
                self._draw_answer_cards(p, w, h)
            else:
                # Level 1/2: Enchanted Forest Theme
                self._draw_sky(p, w, h)
                self._draw_sun(p, w, h)
                self._draw_clouds(p, w, h)
                self._draw_owl_and_bubble(p, w, h)
                self._draw_answer_cards(p, w, h)   # cards drawn BEFORE hills
                self._draw_hills(p, w, h)           # hills cover the bottom of the posts
                self._draw_flowers(p, w, h)
                self._draw_butterflies(p, w, h)

            # Dim overlay when highlighting a specific option (ONLY for L1/L2)
            if self.highlighted_key is not None and self.level < 3:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 100))
                p.drawRect(0, 0, w, h)
                # Redraw ONLY the highlighted card on top of the dim
                self._draw_highlighted_card_on_top(p, w, h)

            self._draw_timer_bar(p, w, h)
        except Exception as e:
            import traceback
            print("Exception in EvaluateGameWidget.paintEvent:")
            traceback.print_exc()
        finally:
            p.end()

    # ═══════════════════ SKY ═══════════════════
    def _draw_sky(self, p, w, h):
        if self.level >= 3:
            # L3: warm sunset tones
            sky = QLinearGradient(0, 0, 0, h * 0.7)
            sky.setColorAt(0, QColor(255, 218, 185))    # peach
            sky.setColorAt(0.7, QColor(255, 235, 210))
            sky.setColorAt(1, QColor(220, 240, 200))
        else:
            # L1/L2: bright blue sky
            sky = QLinearGradient(0, 0, 0, h * 0.7)
            sky.setColorAt(0, QColor(135, 206, 250))
            sky.setColorAt(0.7, QColor(176, 226, 255))
            sky.setColorAt(1, QColor(200, 240, 200))
        p.fillRect(0, 0, w, h, sky)

    # ═══════════════════ SUN ═══════════════════
    def _draw_sun(self, p, w, h):
        sx, sy = w * 0.88, h * 0.08
        # Glow
        glow = QRadialGradient(sx, sy, 100)
        glow.setColorAt(0, QColor(255, 250, 180, 100))
        glow.setColorAt(1, QColor(255, 250, 180, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QPointF(sx, sy), 100, 100)
        # Core
        p.setBrush(QColor(255, 230, 80))
        p.drawEllipse(QPointF(sx, sy), 35, 35)

    # ═══════════════════ CLOUDS ═══════════════════
    def _draw_clouds(self, p, w, h):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 170))
        for cx, cy, cw in [(w * 0.15, h * 0.07, 65), (w * 0.50, h * 0.10, 50), (w * 0.72, h * 0.05, 55)]:
            shift = 8 * math.sin(self.tick * 0.008 + cx)
            for dx, dy, r in [(-cw * 0.3, 0, cw * 0.4), (0, -4, cw * 0.5), (cw * 0.3, 0, cw * 0.35)]:
                p.drawEllipse(QPointF(cx + dx + shift, cy + dy), r, r * 0.55)

    # ═══════════════════ HILLS ═══════════════════
    def _draw_hills(self, p, w, h):
        hill_y = h * 0.72
        path = QPainterPath()
        path.moveTo(0, h)
        path.lineTo(0, hill_y)
        for x in range(0, w + 20, 12):
            hy = hill_y + 25 * math.sin(x * 0.005) + 15 * math.cos(x * 0.011)
            path.lineTo(x, hy)
        path.lineTo(w, h)
        path.closeSubpath()

        grad = QLinearGradient(0, hill_y, 0, h)
        grad.setColorAt(0, QColor(100, 200, 80))
        grad.setColorAt(0.5, QColor(80, 180, 60))
        grad.setColorAt(1, QColor(60, 140, 45))
        p.fillPath(path, grad)

    # ═══════════════════ FLOWERS ═══════════════════
    def _draw_flowers(self, p, w, h):
        p.setPen(Qt.NoPen)
        for fl in self.flowers:
            fx, fy, s = fl.x * w, fl.y * h, fl.size
            # Stem
            p.setPen(QPen(QColor(60, 140, 40), 2))
            p.drawLine(int(fx), int(fy), int(fx), int(fy + s * 1.2))
            p.setPen(Qt.NoPen)
            # Petals
            p.setBrush(fl.color)
            for angle_deg in range(0, 360, 72):
                angle = math.radians(angle_deg)
                px = fx + s * 0.5 * math.cos(angle)
                py = fy + s * 0.5 * math.sin(angle)
                p.drawEllipse(QPointF(px, py), s * 0.35, s * 0.35)
            # Center
            p.setBrush(fl.center_color)
            p.drawEllipse(QPointF(fx, fy), s * 0.25, s * 0.25)

    # ═══════════════════ BUTTERFLIES ═══════════════════
    def _draw_butterflies(self, p, w, h):
        p.setPen(Qt.NoPen)
        for bf in self.butterflies:
            wing = bf.get_wing_spread(self.tick)
            ws = bf.size * wing
            p.setBrush(bf.color)
            p.drawEllipse(QPointF(bf.x - ws * 0.5, bf.y), ws, bf.size * 0.55)
            p.drawEllipse(QPointF(bf.x + ws * 0.5, bf.y), ws, bf.size * 0.55)
            p.setBrush(QColor(60, 40, 30))
            p.drawEllipse(QPointF(bf.x, bf.y), 1.5, bf.size * 0.25)

    # ═══════════════════ OWL + SPEECH BUBBLE ═══════════════════
    def _draw_owl_and_bubble(self, p, w, h):
        if self.level >= 3:
            return  # Background image already has a board for the answer

        # Owl (top-left area)
        owl_h = min(140, int(h * 0.22))
        owl_x = int(w * 0.03)
        owl_y = int(h * 0.03)

        if self.owl_pixmap:
            scaled = self.owl_pixmap.scaledToHeight(owl_h, Qt.SmoothTransformation)
            p.drawPixmap(owl_x, owl_y, scaled)
            bubble_x = owl_x + scaled.width() + 10
        else:
            bubble_x = owl_x + 100

        # Speech bubble
        bubble_y = int(h * 0.04)
        bubble_w = min(int(w * 0.65), w - bubble_x - 30)
        bubble_h = int(h * 0.14)
        bubble_rect = QRectF(bubble_x, bubble_y, bubble_w, bubble_h)

        # Bubble background
        p.setPen(QPen(QColor(255, 255, 255, 200), 2))
        p.setBrush(QColor(255, 255, 255, 230))
        p.drawRoundedRect(bubble_rect, 18, 18)

        # Bubble tail (triangle pointing to owl)
        tail = QPainterPath()
        tail.moveTo(bubble_x, bubble_y + bubble_h * 0.4)
        tail.lineTo(bubble_x - 14, bubble_y + bubble_h * 0.5)
        tail.lineTo(bubble_x, bubble_y + bubble_h * 0.6)
        tail.closeSubpath()
        p.fillPath(tail, QColor(255, 255, 255, 230))
        p.setPen(QPen(QColor(255, 255, 255, 200), 2))
        p.drawPath(tail)

        # Question text
        font_size = 17 if len(self.question_text) > 50 else 20
        p.setFont(QFont("Helvetica", font_size, QFont.Bold))
        p.setPen(QColor(26, 35, 126))  # #1A237E
        text_rect = QRectF(bubble_x + 14, bubble_y + 8, bubble_w - 28, bubble_h - 16)
        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft | Qt.TextWordWrap,
                   self.question_text)

    # ═══════════════════ ANSWER CARDS ═══════════════════
    def _draw_answer_cards(self, p, w, h):
        if not self.options:
            return

        if self.level >= 3:
            # Level 3: Show only the currently highlighted card, centered in the board
            if self.highlighted_key is not None:
                opt = next((o for o in self.options if o.get("key") == self.highlighted_key), None)
                if opt:
                    # Board coordinates in eval3background.png (estimated for 1280x720)
                    board_x, board_y = int(w * 0.28), int(h * 0.28)
                    board_w, board_h = int(w * 0.44), int(h * 0.48)
                    
                    # Draw inside the white board area
                    self._draw_single_card(p, board_x, board_y, board_w, board_h, opt, 1, skip_post=True, l3_mode=True)
            return

        count = len(self.options)
        post_h = 50  # post extends from card bottom into the ground

        if count <= 2:
            # L2/L3: 2 large centered cards
            gap = 30
            card_w = min(280, int((w - gap * 3) / 2))
            card_h = 300
            total_w = card_w * 2 + gap
            start_x = (w - total_w) // 2

            for idx, opt in enumerate(self.options):
                cx = start_x + idx * (card_w + gap)
                card_center_x = cx + card_w / 2
                ground_y = self._get_hill_y(card_center_x, w, h)
                card_y = int(ground_y - card_h - post_h * 0.3)
                self._draw_single_card(p, cx, card_y, card_w, card_h, opt, idx + 1, ground_y)
        else:
            # L1: 4 cards in a row
            gap = 16
            card_w = min(190, int((w - gap * 5) / 4))
            card_h = 260
            total_w = card_w * 4 + gap * 3
            start_x = (w - total_w) // 2

            for idx, opt in enumerate(self.options):
                cx = start_x + idx * (card_w + gap)
                card_center_x = cx + card_w / 2
                ground_y = self._get_hill_y(card_center_x, w, h)
                card_y = int(ground_y - card_h - post_h * 0.3)
                self._draw_single_card(p, cx, card_y, card_w, card_h, opt, idx + 1, ground_y)

    def _draw_single_card(self, p, x, y, w, h, opt, num, ground_y=None, skip_post=False, l3_mode=False):
        """Draw one answer signpost card planted in the ground."""
        key = opt.get("key", "")
        card_rect = QRectF(x, y, w, h)

        if not l3_mode:
            # Highlight state
            is_highlighted = (key == self.highlighted_key)
            if is_highlighted and self.highlight_correct is True:
                border_color = QColor(46, 125, 50)
                bg_color = QColor(200, 255, 200, 240)
                border_w = 5
            elif (is_highlighted and self.highlight_correct is False) or (key in getattr(self, "wrong_keys", set())):
                border_color = QColor(211, 47, 47)
                bg_color = QColor(255, 210, 210, 240)
                border_w = 5
            elif is_highlighted and self.highlight_correct == "present":
                border_color = QColor(25, 118, 210)  # Blue for presenting
                bg_color = QColor(227, 242, 253, 240)
                border_w = 5
            else:
                border_color = QColor(200, 180, 140, 180)
                bg_color = QColor(255, 253, 245, 235)
                border_w = 3

            # Wooden post from card bottom INTO the ground (skip when redrawing on top of dim)
            if not skip_post:
                post_w = 12
                post_top = int(y + h)
                post_bottom = int(ground_y + 40) if ground_y else int(y + h + 50)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(120, 80, 40))
                p.drawRect(int(x + w / 2 - post_w / 2), post_top, post_w, post_bottom - post_top)

            # Card shadow
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 20))
            p.drawRoundedRect(QRectF(x + 3, y + 4, w, h), 18, 18)

            # Card body
            p.setPen(QPen(border_color, border_w))
            p.setBrush(bg_color)
            p.drawRoundedRect(card_rect, 18, 18)

        # Content (Image + Text)
        pix = opt.get("pixmap")
        label = opt.get("label", "")

        if l3_mode:
            # For Level 3, use maximum image area within the underwater board
            img_h = int(h * 0.9)
            text_y_offset = 0  # No text in L3
        else:
            img_h = int(h * 0.6)
            text_y_offset = int(h * 0.75)

        if pix and not pix.isNull():
            scaled_pix = pix.scaledToHeight(img_h, Qt.SmoothTransformation)
            px = x + (w - scaled_pix.width()) / 2
            py = y + (img_h - scaled_pix.height()) / 2
            
            # ── GLOW EFFECT (L3 Focus Mode) ──
            if l3_mode and getattr(self, "focus_mode", False):
                glow_r = max(1.0, max(scaled_pix.width(), scaled_pix.height()) * 0.8)
                glow = QRadialGradient(px + scaled_pix.width()/2, py + scaled_pix.height()/2, glow_r)
                glow.setColorAt(0, QColor(255, 255, 220, 150)) # Soft warm white
                glow.setColorAt(1, QColor(255, 255, 220, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(glow)
                p.drawEllipse(QPointF(px + scaled_pix.width()/2, py + scaled_pix.height()/2), glow_r, glow_r)

            p.drawPixmap(int(px), int(py), scaled_pix)
        
        # Label (Only for L1/L2)
        if not l3_mode:
            p.setPen(QColor(40, 40, 40))
            p.setFont(QFont("Helvetica", 18, QFont.Bold))
            text_rect = QRectF(x + 10, y + text_y_offset, w - 20, 40)
            p.drawText(text_rect, Qt.AlignCenter, label)

            # Index badge (bottom-right)
            badge_r = 18
            badge_x = x + w - badge_r - 8
            badge_y = y + h - badge_r - 8
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(25, 118, 210))  # #1976D2
            p.drawEllipse(QPointF(badge_x, badge_y), badge_r, badge_r)

            p.setFont(QFont("Helvetica", 14, QFont.Bold))
            p.setPen(QColor(255, 255, 255))
            p.drawText(QRectF(badge_x - badge_r, badge_y - badge_r, badge_r * 2, badge_r * 2),
                    Qt.AlignCenter, str(num))

    # ═══════════════════ TIMER BAR ═══════════════════
    def _draw_timer_bar(self, p, w, h):
        bar_h = 16
        bar_y = int(h - bar_h - 8)
        margin = int(w * 0.05)
        bar_w = w - margin * 2

        # Background track (white, semi-transparent)
        p.setPen(QPen(QColor(255, 255, 255, 150), 2))
        p.setBrush(QColor(255, 255, 255, 120))
        p.drawRoundedRect(QRectF(margin, bar_y, bar_w, bar_h), bar_h / 2, bar_h / 2)

        # Progress fill
        fill_w = bar_w * self.timer_progress
        if self.timer_progress > 0.5:
            fill_color = QColor(76, 175, 80)
        elif self.timer_progress > 0.2:
            fill_color = QColor(255, 193, 7)
        else:
            fill_color = QColor(244, 67, 54)

        p.setPen(Qt.NoPen)
        p.setBrush(fill_color)
        if fill_w > 0:
            p.drawRoundedRect(QRectF(margin, bar_y, fill_w, bar_h), bar_h / 2, bar_h / 2)

    def _draw_highlighted_card_on_top(self, p, w, h):
        """Redraw only the highlighted card above the dim overlay."""
        if not self.options or self.highlighted_key is None:
            return

        count = len(self.options)
        post_h = 50

        if count <= 2:
            gap = 30
            card_w = min(280, int((w - gap * 3) / 2))
            card_h = 300
            total_w = card_w * 2 + gap
            start_x = (w - total_w) // 2

            for idx, opt in enumerate(self.options):
                if opt.get("key") == self.highlighted_key:
                    cx = start_x + idx * (card_w + gap)
                    card_center_x = cx + card_w / 2
                    ground_y = self._get_hill_y(card_center_x, w, h)
                    card_y = int(ground_y - card_h - post_h * 0.3)
                    self._draw_single_card(p, cx, card_y, card_w, card_h, opt, idx + 1, ground_y, skip_post=True)
        else:
            gap = 16
            card_w = min(190, int((w - gap * 5) / 4))
            card_h = 260
            total_w = card_w * 4 + gap * 3
            start_x = (w - total_w) // 2

            for idx, opt in enumerate(self.options):
                if opt.get("key") == self.highlighted_key:
                    cx = start_x + idx * (card_w + gap)
                    card_center_x = cx + card_w / 2
                    ground_y = self._get_hill_y(card_center_x, w, h)
                    card_y = int(ground_y - card_h - post_h * 0.3)
                    self._draw_single_card(p, cx, card_y, card_w, card_h, opt, idx + 1, ground_y, skip_post=True)

    def reset(self):
        """Clear all state for a fresh evaluation."""
        self.question_text = ""
        self.options = []
        self.highlighted_key = None
        self.highlight_correct = None
        self.wrong_keys = set()
        self.timer_progress = 1.0
        self.update()
