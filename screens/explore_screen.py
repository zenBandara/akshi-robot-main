import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer, QUrl
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPainterPath, QRegion
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
media_player = None
audio_output = None
video_widget = None

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
    """Dynamically hot-swaps the underlying QMediaPlayer layer matching the precise exploration vocal queue."""
    global media_player
    if not media_player:
        return
        
    urls_dict = explore_data.get("video_urls", {})
    media_url = urls_dict.get(stage, "")
    abs_media_path = os.path.join(project_root, media_url) if media_url else ""
    
    if os.path.exists(abs_media_path):
        media_player.setSource(QUrl.fromLocalFile(abs_media_path))
        media_player.setLoops(QMediaPlayer.Infinite)
        media_player.play()
        print(f"[Explore Screen] Video playing stage '{stage}': {abs_media_path}")
    else:
        print(f"[Explore Screen] Video file not found for stage '{stage}': {abs_media_path}")

def setup_video_container():
    global media_player, audio_output, video_widget
    
    if media_player:
        media_player.stop()
        media_player.deleteLater()
        media_player = None
        
    video_widget = QVideoWidget()
    video_widget.setAspectRatioMode(Qt.KeepAspectRatioByExpanding)
    
    container = window.video_container
    if container.layout() is None:
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
    else:
        while container.layout().count():
            item = container.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    container.layout().addWidget(video_widget)
    
    # Beautiful styling mapping to the Explore screen's theme
    container.setStyleSheet("background-color: #F8BBD0; border-radius: 20px; border: 4px dashed #D81B60;") 
    QTimer.singleShot(100, lambda: apply_rounded_clip(container, 20))
    
    audio_output = QAudioOutput()
    audio_output.setVolume(0)
    
    media_player = QMediaPlayer()
    media_player.setAudioOutput(audio_output)
    media_player.setVideoOutput(video_widget)


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
        if media_player:
            media_player.stop()
            
        print("[Explore Screen] Student pressed ENTER. End exploration phase and continuing cascade!")
        
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.advance_cascade(parent_stack)
        except ImportError: pass
