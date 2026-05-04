import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer, QUrl
from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtGui import QPainterPath, QRegion, QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "kinestaticUI.ui")

window = None
input_enabled = False
voice_manager = VoiceManager()
video_label = None
frame_timer = None
current_frames = []
current_frame_idx = 0

def get_ui():
    global window
    if window is None:
        loader = QUiLoader()
        file = QFile(ui_path)
        if not file.open(QFile.ReadOnly):
            print("Cannot open UI file:", ui_path)
            return None
        window = loader.load(file)
        file.close()
        
        window.on_show = on_show
        
    return window

def apply_rounded_clip(widget, radius=20):
    from PySide6.QtCore import QRectF
    path = QPainterPath()
    path.addRoundedRect(QRectF(widget.rect()), radius, radius)
    region = QRegion(path.toFillPolygon().toPolygon())
    widget.setMask(region)

def swap_video(stage, kinesthetic_data):
    """Dynamically hot-swaps the underlying image sequence layer matching the vocal queue."""
    global current_frames, current_frame_idx, frame_timer
    
    urls_dict = kinesthetic_data.get("video_urls", {})
    media_url = urls_dict.get(stage, "")
    
    if not media_url:
        return
        
    # Example media_url: "assets/video/t_1-kin-start.mp4"
    # We strip the extension to get the directory containing the frames
    base_dir = media_url.rsplit('.', 1)[0]
    abs_dir_path = os.path.join(project_root, base_dir)
    
    if os.path.isdir(abs_dir_path):
        # Gather all frame_*.jpg
        frames = [os.path.join(abs_dir_path, f) for f in os.listdir(abs_dir_path) if f.endswith('.jpg')]
        frames.sort()
        current_frames = frames
        current_frame_idx = 0
        if current_frames and frame_timer:
            frame_timer.start(66) # 15 FPS (~66ms)
            print(f"[Kinesthetic Screen] Image sequence playing stage '{stage}': {abs_dir_path}")
    else:
        print(f"[Kinesthetic Screen] Image sequence dir not found for stage '{stage}': {abs_dir_path}")

def update_frame():
    global current_frames, current_frame_idx, video_label
    if current_frames and video_label:
        pixmap = QPixmap(current_frames[current_frame_idx])
        video_label.setPixmap(pixmap)
        current_frame_idx = (current_frame_idx + 1) % len(current_frames)

def setup_video_container():
    global video_label, frame_timer
    
    if frame_timer:
        frame_timer.stop()
        
    if video_label is None:
        video_label = QLabel()
        video_label.setAlignment(Qt.AlignCenter)
        video_label.setScaledContents(True) # Fills container smoothly
        
    container = window.video_container
    if container.layout() is None:
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
    else:
        while container.layout().count():
            item = container.layout().takeAt(0)
            if item.widget() and item.widget() != video_label:
                item.widget().deleteLater()
    
    if container.layout().indexOf(video_label) == -1:
        container.layout().addWidget(video_label)
    
    # Beautiful styling for the kinesthetic screen container
    container.setStyleSheet("background-color: #E8F5E9; border-radius: 20px;")
    QTimer.singleShot(100, lambda: apply_rounded_clip(container, 20))
    
    if frame_timer is None:
        frame_timer = QTimer()
        frame_timer.timeout.connect(update_frame)


def on_show():
    global input_enabled
    print("[Kinesthetic Screen] Becoming active...")
    state_manager.set_current_screen("kinesthetic")
    
    input_enabled = False
    voice_manager.stop()
    
    task_data = state_manager.get_current_task()
    kinesthetic_data = task_data.get("kinesthetic", {}) if task_data else {}
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    
    window.title_label.setText(kinesthetic_data.get("task_title", "Kinesthetic Learning"))
    
    # Boot UI Video Infrastructure
    setup_video_container()
    
    speech_start = kinesthetic_data.get("speech_start", "")
    speech_step_1 = kinesthetic_data.get("speech_step_1", "")
    speech_step_2 = kinesthetic_data.get("speech_step_2", "")
    speech_end = kinesthetic_data.get("speech_end", "")
    
    get_robot_eyes().set_expression("thinking")
    
    def step_4():
        if not input_enabled: return
        swap_video("end", kinesthetic_data)
        get_robot_eyes().set_expression("default")
        if speech_end:
            window.robot_text_label.setText(f"🤖 \"{speech_end}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_end}\"")
            voice_manager.speak(speech_end, f"kin_{student_name}_end")
        
    def step_3():
        if not input_enabled: return
        swap_video("step_2", kinesthetic_data)
        get_robot_eyes().set_expression("surprised")
        if speech_step_2:
            window.robot_text_label.setText(f"🤖 \"{speech_step_2}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_step_2}\"")
            delay = voice_manager.speak(speech_step_2, f"kin_{student_name}_step2")
            QTimer.singleShot(delay + 600, step_4)
        else:
            step_4()
            
    def step_2():
        if not input_enabled: return
        swap_video("step_1", kinesthetic_data)
        get_robot_eyes().set_expression("encouraging")
        if speech_step_1:
            window.robot_text_label.setText(f"🤖 \"{speech_step_1}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_step_1}\"")
            delay = voice_manager.speak(speech_step_1, f"kin_{student_name}_step1")
            QTimer.singleShot(delay + 600, step_3)
        else:
            step_3()
            
    if speech_start:
        swap_video("start", kinesthetic_data)
        window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
        print(f"🤖 ROBOT SPEAKS: \"{speech_start}\"")
        start_delay = voice_manager.speak(speech_start, f"kin_{student_name}_start")
        QTimer.singleShot(start_delay + 600, step_2)
    else:
        step_2()
        
    # Enable bypass immediately
    print("[Kinesthetic Screen] Enabling keyboard block natively for developer bypass")
    enable_input()


def enable_input():
    global input_enabled
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)


def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action in ("P", "ENTER"): # Teacher Overrides - PASS (P key or "OK" voice command)
        input_enabled = False
        voice_manager.stop()
        if frame_timer:
            frame_timer.stop()
        print("[Kinesthetic Screen] Teacher approved! Moving on to next student...")
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.on_correct_answer(parent_stack) # Passed fallback, skip next student
        except ImportError: pass
            
    elif action in ("F", "NO"): # Teacher Overrides - FAIL (F key or "No" voice command)
        input_enabled = False
        voice_manager.stop()
        if frame_timer:
            frame_timer.stop()
        print("[Kinesthetic Screen] Teacher failed student. Proceeding down cascade.")
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.on_incorrect_answer(parent_stack)
        except ImportError: pass