import os
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect

def fade_in_widget(widget, duration=400):
    """Applies a smooth fade-in opacity animation to a physically requested widget."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    
    # Must securely bind the native QPropertyAnimation to the widget namespace natively
    # so the Python garbage collector doesn't brutally destroy the C++ pointer loop mid-animation.
    widget._fade_anim = QPropertyAnimation(effect, b"opacity")
    widget._fade_anim.setDuration(duration)
    widget._fade_anim.setStartValue(0.0)
    widget._fade_anim.setEndValue(1.0)
    widget._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
    widget._fade_anim.start()

def switch_screen(parent_stack, new_widget):
    """Safely transitions a global QStackedWidget to new_widget with a seamless fade-in curve."""
    if parent_stack and new_widget:
        parent_stack.addWidget(new_widget)
        parent_stack.setCurrentWidget(new_widget)
        fade_in_widget(new_widget)
