import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes

voice_manager = VoiceManager()
window = None
frame_timer = None
current_frames = []
current_frame_idx = 0

def get_ui():
    global window
    if window is None:
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        ui_path = os.path.join(project_root, "ui", "waterBreakUI.ui")

        loader = QUiLoader()
        file = QFile(ui_path)
        if not file.open(QFile.ReadOnly):
            print("Cannot open UI file:", ui_path)
            return None

        window = loader.load(file)
        file.close()

        window.on_show = on_show
    return window

def on_show():
    global frame_timer, current_frames, current_frame_idx
    print("[Water Break Screen] Becoming active...")
    state_manager.set_current_screen("water_break")
    get_robot_eyes().set_expression("sleeping")
    keyboard_manager.register_handler(handle_key_press)
    
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
    frame_timer.start(100) # 10 FPS
    
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    
    speech = f"Hey {student_name}, you've been sitting there for a little while! I think it's the perfect time for a quick water break. Go grab a nice drink, and when you are all ready, come back and press Enter!"
    print(f"🤖 ROBOT SPEAKS (Water Break): \"{speech}\"")
    voice_manager.speak(speech, f"water_break_{student_name}")

def update_frame():
    global current_frames, current_frame_idx, window
    if current_frames and window and hasattr(window, 'video_label'):
        pixmap = QPixmap(current_frames[current_frame_idx])
        scaled_pixmap = pixmap.scaled(window.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        window.video_label.setPixmap(scaled_pixmap)
        current_frame_idx = (current_frame_idx + 1) % len(current_frames)

def handle_key_press(action):
    global frame_timer
    if action in ["ENTER", "YES"]:
        if frame_timer:
            frame_timer.stop()
        voice_manager.stop()
        get_robot_eyes().set_expression("surprised")
        
        student_name = str(state_manager.get_current_student() or "friend").capitalize()
        speech = f"Yay {student_name}! Welcome back! You look refreshed! Let's try again!"
        delay_ms = voice_manager.speak(speech, f"water_break_welcome_{student_name}")
        
        keyboard_manager.unregister_handler()
        
        def resume():
            from core.flow_controller import flow_controller
            flow_controller.resume_cascade(window.parentWidget())
            
        QTimer.singleShot(delay_ms, resume)
