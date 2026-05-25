import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QGraphicsOpacityEffect
from PySide6.QtGui import QPixmap, QFont, QPainterPath, QRegion
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator
from core.voice_manager import VoiceManager
from core.stream_control import set_frame_streaming
from components.robot_eyes import get_robot_eyes

voice_manager = VoiceManager()
window = None
frame_timer = None
current_frames = []
current_frame_idx = 0
input_enabled = False


def get_ui():
    global window
    if window is None:
        window = QWidget()
        window.setObjectName("WaterBreakScreen")
        window.setStyleSheet("QWidget#WaterBreakScreen { background-color: #E3F2FD; }")

        main_layout = QVBoxLayout(window)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(15)

        # ── Title Label ──
        title_label = QLabel("💧 Water Break Time! 💧")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #1565C0;
                font-size: 42px;
                font-weight: bold;
                background: transparent;
            }
        """)
        main_layout.addWidget(title_label)

        # ── Video Container ──
        video_container = QFrame()
        video_container.setObjectName("video_container")
        video_container.setStyleSheet("""
            QFrame {
                background-color: #BBDEFB;
                border-radius: 20px;
                border: 4px solid #90CAF9;
            }
        """)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)

        video_label = QLabel()
        video_label.setObjectName("video_label")
        video_label.setAlignment(Qt.AlignCenter)
        video_label.setScaledContents(True)
        video_layout.addWidget(video_label)

        main_layout.addWidget(video_container, 1)  # Stretch to fill

        # ── Robot Speech Bubble ──
        robot_text_label = QLabel("")
        robot_text_label.setObjectName("robot_text_label")
        robot_text_label.setAlignment(Qt.AlignCenter)
        robot_text_label.setWordWrap(True)
        robot_text_label.setStyleSheet("""
            QLabel {
                color: #1565C0;
                font-size: 22px;
                font-style: italic;
                background: transparent;
                padding: 8px 20px;
            }
        """)
        main_layout.addWidget(robot_text_label)

        # ── Hint Label ──
        hint_label = QLabel("Say 'Okay' when you're back! 🌟")
        hint_label.setObjectName("hint_label")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("""
            QLabel {
                color: #1976D2;
                font-size: 26px;
                font-weight: bold;
                background-color: #FFFFFF;
                border-radius: 15px;
                border: 3px solid #90CAF9;
                padding: 12px 30px;
            }
        """)
        main_layout.addWidget(hint_label)

        window.on_show = on_show
    return window


def on_show():
    global frame_timer, current_frames, current_frame_idx, input_enabled
    print("[Water Break Screen] Becoming active...")
    state_manager.set_current_screen("water_break")
    get_robot_eyes().set_expression("sleeping")

    # Stop tracking the face while the student is drinking water
    try:
        set_frame_streaming(False, reason="water_break")
    except Exception:
        pass

    input_enabled = False
    voice_manager.stop()

    project_root = os.path.dirname(os.path.dirname(__file__))
    video_dir = os.path.join(project_root, "assets", "video", "water_break")

    if os.path.isdir(video_dir):
        frames = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith('.jpg')]
        frames.sort()
        current_frames = frames
        current_frame_idx = 0
    else:
        print(f"[Water Break Screen] Video sequence not found: {video_dir}")
        current_frames = []

    if frame_timer is None:
        frame_timer = QTimer()
        frame_timer.timeout.connect(update_frame)
    frame_timer.start(100)  # 10 FPS

    student_name = str(state_manager.get_current_student() or "friend").capitalize()

    # Update robot speech bubble
    robot_text = window.findChild(QLabel, "robot_text_label")
    speech = (
        f"Hey {student_name}, you've been working so hard! "
        f"I think it's the perfect time for a quick water break. "
        f"Go grab a nice drink of water, and when you're ready, come back and say Okay!"
    )
    if robot_text:
        robot_text.setText(f'🤖 "{speech}"')

    print(f'🤖 ROBOT SPEAKS (Water Break): "{speech}"')
    delay_ms = voice_manager.speak(speech, f"water_break_{student_name}")

    # Enable input after speech finishes
    QTimer.singleShot(delay_ms + 300, enable_input)


def enable_input():
    global input_enabled
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)
    print("[Water Break Screen] Keyboard input enabled. Waiting for student to say 'Okay'.")


def update_frame():
    global current_frames, current_frame_idx, window
    if current_frames and window:
        video_label = window.findChild(QLabel, "video_label")
        if video_label:
            pixmap = QPixmap(current_frames[current_frame_idx])
            video_label.setPixmap(pixmap)
            current_frame_idx = (current_frame_idx + 1) % len(current_frames)


def handle_key_press(action):
    global frame_timer, input_enabled
    if not input_enabled:
        return

    if action in ["ENTER", "YES"]:
        input_enabled = False
        if frame_timer:
            frame_timer.stop()
        voice_manager.stop()
        keyboard_manager.unregister_handler()
        get_robot_eyes().set_expression("surprised")

        student_name = str(state_manager.get_current_student() or "friend").capitalize()
        speech = f"Yay {student_name}! Welcome back! You look so refreshed! Let's try again!"
        print(f'🤖 ROBOT SPEAKS (Welcome Back): "{speech}"')
        delay_ms = voice_manager.speak(speech, f"water_break_welcome_{student_name}")

        def resume():
            from core.flow_controller import flow_controller
            flow_controller.resume_cascade(window.parentWidget())

        print("[Water Break Screen] Student said Okay/Yes. Resuming cascade.")
        QTimer.singleShot(delay_ms, resume)
