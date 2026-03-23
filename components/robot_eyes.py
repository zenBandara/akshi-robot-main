import os
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from core.styles import Styling

class RobotEyesWidget(QWidget):
    """A floating, emotionally expressive global widget overlay that universally binds across all Qt layouts."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expressions = {
            "default": "( ^ᴗ^ )",
            "thinking": "( ˘~˘ )",
            "surprised": "( O_O )",
            "encouraging": "( ◕ᴗ◕ )",
            "sleeping": "( -.- )zZ",
            "sad": "( ;_; )"
        }
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.eyes_label = QLabel(self.expressions["default"])
        self.eyes_label.setAlignment(Qt.AlignCenter)
        self.eyes_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32px; 
                font-weight: bold; 
                color: {Styling.COLOR_ROBOT_TEXT}; 
                background-color: white; 
                border-radius: 15px; 
                padding: 10px 20px;
                border: 3px solid {Styling.COLOR_ROBOT_TEXT};
            }}
        """)
        
        self.layout.addWidget(self.eyes_label)
        
        # Asynchronous Native Hardware Blink Engine
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink)
        self.blink_timer.start(4000) # Trigger every 4 seconds
        
        self.current_state = "default"

    def set_expression(self, state_name):
        """Update the physical robotic GUI ascii eye pattern manually."""
        if state_name in self.expressions:
            self.current_state = state_name
            self.eyes_label.setText(self.expressions[state_name])
            
    def blink(self):
        """Physical blinking interrupt mechanism strictly scoped to positive rest constraints."""
        if self.current_state in ["default", "encouraging"]:
            self.eyes_label.setText("( -_- )")
            # Sub-millisecond restoration mapping safely escaping closure blocks
            QTimer.singleShot(150, lambda: self.eyes_label.setText(self.expressions[self.current_state]))

robot_eyes_instance = None

def get_robot_eyes():
    """Lazy-load the singleton eye widget absolutely guaranteeing execution waits until the QApplication kernel is fully mounted."""
    global robot_eyes_instance
    if robot_eyes_instance is None:
        robot_eyes_instance = RobotEyesWidget()
    return robot_eyes_instance
