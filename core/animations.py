from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup

def apply_pulse_glow(widget, base_style=None, glow_style=None):
    """
    Applies an infinitely looping opacity pulse and border-color glow animation smoothly.
    Returns the QParallelAnimationGroup (caller MUST keep a reference, e.g. appending to a list).
    """
    if base_style is None:
        base_style = "QFrame { background-color: white; border-radius: 25px; border: 4px solid #4DD0E1; }"
    if glow_style is None:
        glow_style = "QFrame { background-color: #E0F7FA; border-radius: 25px; border: 6px solid #00ACC1; }"
        
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    pulse = QPropertyAnimation(effect, b"opacity")
    pulse.setDuration(1200)  # Gentle speed for kids
    pulse.setStartValue(1.0)
    pulse.setKeyValueAt(0.5, 0.75)  # Don't fade out too much, keep it readable
    pulse.setEndValue(1.0)
    pulse.setLoopCount(-1)
    pulse.setEasingCurve(QEasingCurve.InOutSine)

    glow = QPropertyAnimation(widget, b"styleSheet")
    glow.setDuration(1200)
    glow.setKeyValueAt(0.0, base_style)
    glow.setKeyValueAt(0.5, glow_style)
    glow.setKeyValueAt(1.0, base_style)
    glow.setLoopCount(-1)

    group = QParallelAnimationGroup()
    group.addAnimation(pulse)
    group.addAnimation(glow)

    group.start()
    return group
