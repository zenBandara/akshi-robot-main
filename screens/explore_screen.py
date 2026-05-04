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
ui_path = os.path.join(project_root, "ui", "exploreUI.ui")

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

def swap_video(stage, explore_data):
    """Dynamically hot-swaps the underlying image sequence layer matching the precise exploration vocal queue."""
    global current_frames, current_frame_idx, frame_timer
    
    urls_dict = explore_data.get("video_urls", {})
    media_url = urls_dict.get(stage, "")
    
    if not media_url:
        return
        
    base_dir = media_url.rsplit('.', 1)[0]
    abs_dir_path = os.path.join(project_root, base_dir)
    
    if os.path.isdir(abs_dir_path):
        frames = [os.path.join(abs_dir_path, f) for f in os.listdir(abs_dir_path) if f.endswith('.jpg')]
        frames.sort()
        current_frames = frames
        current_frame_idx = 0
        if current_frames and frame_timer:
            frame_timer.start(66) # 15 FPS (~66ms)
            print(f"[Explore Screen] Image sequence playing stage '{stage}': {abs_dir_path}")
    else:
        print(f"[Explore Screen] Image sequence dir not found for stage '{stage}': {abs_dir_path}")

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
        video_label.setScaledContents(True)
    
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
    
    # Beautiful styling mapping to the Explore screen's theme
    container.setStyleSheet("background-color: #F8BBD0; border-radius: 20px; border: 4px dashed #D81B60;") 
    QTimer.singleShot(100, lambda: apply_rounded_clip(container, 20))
    
    if frame_timer is None:
        frame_timer = QTimer()
        frame_timer.timeout.connect(update_frame)


def on_show():
    global input_enabled
    print("[Explore Screen] Becoming active...")
    state_manager.set_current_screen("explore")
    
    task_data = state_manager.get_current_task()
    if not task_data or "explore" not in task_data:
        print("Error: No valid explore task found in state_manager.")
        window.title_label.setText("Error: Task not loaded.")
        return
        
    explore_data = task_data.get("explore", {})
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    
    input_enabled = False
    voice_manager.stop()
    
    window.title_label.setText(explore_data.get("task_title", "Let's Explore!"))
    
    # Initialize UI video player
    setup_video_container()
        
    # Safari Adventure Speech Implementation
    speech_start = explore_data.get("speech_start", "Let's begin our adventure!")
    speech_middle = explore_data.get("speech_middle", "Look closely!")
    speech_end = explore_data.get("speech_end", "Press the Enter key when you are done!")
    
    get_robot_eyes().set_expression("encouraging")
    
    def complete_explore():
        if not input_enabled: return
        swap_video("end", explore_data)
        get_robot_eyes().set_expression("default")
        if speech_end:
            window.robot_text_label.setText(f"🤖 \"{speech_end}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_end}\"")
            voice_manager.speak(speech_end, f"expl_{student_name}_end")
            
    def play_middle():
        if not input_enabled: return
        swap_video("step_1", explore_data)
        get_robot_eyes().set_expression("surprised")
        if speech_middle:
            window.robot_text_label.setText(f"🤖 \"{speech_middle}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_middle}\"")
            delay = voice_manager.speak(speech_middle, f"expl_{student_name}_mid")
            QTimer.singleShot(delay + 600, complete_explore)
        else:
            complete_explore()
            
    if speech_start:
        swap_video("start", explore_data)
        window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
        print(f"🤖 ROBOT SPEAKS: \"{speech_start}\"")
        start_delay = voice_manager.speak(speech_start, f"expl_{student_name}_start")
        QTimer.singleShot(start_delay + 600, play_middle)
    else:
        play_middle()
        
    print(f"[Explore Screen] Enabling keyboard input immediately to allow for speech interruption.")
    enable_input()


def enable_input():
    global input_enabled
    input_enabled = True
    print("[Explore Screen] Robot fully finished speaking. Keyboard hardware inputs physically enabled.")
    keyboard_manager.register_handler(handle_key_press)


def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action == "ENTER":
        input_enabled = False
        voice_manager.stop()
        if frame_timer:
            frame_timer.stop()
            
        print("[Explore Screen] Student pressed ENTER. End exploration phase and continuing cascade!")
        
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.advance_cascade(parent_stack)
        except ImportError: pass
