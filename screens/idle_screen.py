import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QPropertyAnimation, Qt, QUrl
from PySide6.QtWidgets import QGraphicsOpacityEffect, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from core.keyboard_manager import keyboard_manager
from core.state_manager import state_manager
from core.navigator import navigator

window = None
pulse_anim = None
fade_effect = None
video_label = None
frame_timer = None
current_frames = []
current_frame_idx = 0

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    ui_path = os.path.join(project_root, "ui", "idleUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    setup_animations()
    
    # Standardize lifecycle hooks for Navigator
    def on_show():
        print("[Idle Screen] Becoming active with native Video Engine...")
        keyboard_manager.register_handler(handle_key_press)
        state_manager.set_current_screen("idle")
        
        # Deploy image sequence pipeline gracefully
        if frame_timer is None:
            setup_video()
        else:
            frame_timer.start(66)

    window.on_show = on_show
    return window

def setup_animations():
    global window, pulse_anim, fade_effect
    
    # 1. Slow glowing pulse for the hint label natively
    fade_effect = QGraphicsOpacityEffect(window.hint_label)
    window.hint_label.setGraphicsEffect(fade_effect)
    
    pulse_anim = QPropertyAnimation(fade_effect, b"opacity")
    pulse_anim.setDuration(2500)
    pulse_anim.setStartValue(0.2)
    pulse_anim.setKeyValueAt(0.5, 1.0)
    pulse_anim.setEndValue(0.2)
    pulse_anim.setLoopCount(-1) # Infinite loop
    pulse_anim.start()

def setup_video():
    global window, video_label, frame_timer, current_frames, current_frame_idx
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    video_dir = os.path.join(project_root, "assets", "video", "idle")
    
    if video_label is None:
        video_label = QLabel()
        video_label.setAlignment(Qt.AlignCenter)
        video_label.setScaledContents(True)
    
    # Dynamically mount directly into the centralized Web Container GUI layout frame
    layout = QVBoxLayout(window.web_container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(video_label)
    
    if os.path.isdir(video_dir):
        frames = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith('.jpg')]
        frames.sort()
        current_frames = frames
        current_frame_idx = 0
    else:
        print(f"[Idle Screen] Idle image sequence not found: {video_dir}")
        return
        
    if frame_timer is None:
        frame_timer = QTimer()
        frame_timer.timeout.connect(update_frame)
    frame_timer.start(66) # ~15 FPS

def update_frame():
    global current_frames, current_frame_idx, video_label
    if current_frames and video_label:
        pixmap = QPixmap(current_frames[current_frame_idx])
        video_label.setPixmap(pixmap)
        current_frame_idx = (current_frame_idx + 1) % len(current_frames)

def handle_key_press(mapped_action):
    global frame_timer
    if mapped_action == "WAKE":
        print("[Idle Screen] WAKE command triggered! Transitioning natively to Greeting...")
        if frame_timer is not None:
            frame_timer.stop()
        navigator.navigate_to("greeting")
