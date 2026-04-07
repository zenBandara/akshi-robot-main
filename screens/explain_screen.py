import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer, QUrl
from PySide6.QtGui import QPixmap, QImage, QPainterPath, QRegion
from PySide6.QtWidgets import QVBoxLayout, QFrame
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "explainUI.ui")

window = None
input_enabled = False
explain_data = {}
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

def on_show():
    print("[Explain Screen] Becoming active...")
    state_manager.set_current_screen("explain")
    
    task_data = state_manager.get_current_task()
    if not task_data or "explain" not in task_data:
        print("Error: No valid explain task found in state_manager.")
        window.title_label.setText("Error: Task not loaded.")
        return
        
    explain_data = task_data.get("explain", {})
    
    # 1. Populate Title
    window.title_label.setText(explain_data.get("task_title", "Let's Understand This Better!"))
    
    # 2. Setup Video — following exact idle_screen.py pattern
    setup_video(explain_data)
    
    # 3. Speech
    speech_start = explain_data.get("speech_start", "Let's review this concept together.")
    speech_end = explain_data.get("speech_end", "Press Enter when you are done.")
    full_speech = f"{speech_start} {speech_end}"
    
    window.robot_text_label.setText(f'🤖 "{full_speech}"')
    print(f'🤖 ROBOT SPEAKS: "{full_speech}"')
    voice_manager.speak(full_speech, f"explain_full_{task_data.get('task_id', 'id')}")
    
    enable_input()

def apply_rounded_clip(widget, radius=20):
    """Apply a rounded rectangle clip mask to a widget so its children are visually clipped."""
    from PySide6.QtCore import QRectF
    path = QPainterPath()
    path.addRoundedRect(QRectF(widget.rect()), radius, radius)
    region = QRegion(path.toFillPolygon().toPolygon())
    widget.setMask(region)

def setup_video(explain_data):
    """Setup video player following the proven idle_screen.py architecture."""
    global media_player, audio_output, video_widget
    
    # Resolve video path
    media_url = explain_data.get("video_url", "")
    if not media_url:
        media_url = "assets/video/t_1-explain.mp4"
    
    abs_media_path = os.path.join(project_root, media_url)
    if not os.path.exists(abs_media_path):
        abs_media_path = os.path.join(project_root, "assets", "video", "t_1-explain.mp4")
    
    # Cleanup old player
    if media_player:
        media_player.stop()
        media_player.deleteLater()
        media_player = None
    
    # Create QVideoWidget exactly like idle_screen.py
    video_widget = QVideoWidget()
    
    # Expand to fill, eliminating black letterbox bars
    video_widget.setAspectRatioMode(Qt.KeepAspectRatioByExpanding)
    
    # Mount into the container layout (same pattern as idle_screen.py web_container)
    container = window.video_container
    
    # If container doesn't have a layout yet, create one
    if container.layout() is None:
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
    else:
        # Clear existing widgets
        while container.layout().count():
            item = container.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        container.layout().setContentsMargins(0, 0, 0, 0)
    
    container.layout().addWidget(video_widget)
    
    # Apply rounded corner clip mask to the container (clips the QVideoWidget inside)
    container.setStyleSheet("background-color: #FFF3E0; border: 4px solid #FFCC80; border-radius: 20px;")
    QTimer.singleShot(100, lambda: apply_rounded_clip(container, 20))
    
    # Audio output (muted — robot voice handles narration)
    audio_output = QAudioOutput()
    audio_output.setVolume(0)
    
    # Media player
    media_player = QMediaPlayer()
    media_player.setAudioOutput(audio_output)
    media_player.setVideoOutput(video_widget)
    
    if os.path.exists(abs_media_path):
        media_player.setSource(QUrl.fromLocalFile(abs_media_path))
        media_player.setLoops(QMediaPlayer.Infinite)
        media_player.play()
        print(f"[Explain Screen] Video playing: {abs_media_path}")
    else:
        print(f"[Explain Screen] Video file not found: {abs_media_path}")

def play_second_speech():
    pass # Deprecated by combined fluent speech

def enable_input():
    global input_enabled
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)
    window.robot_text_label.setText("🤖 Press Enter when you are done.")
    print("[Explain Screen] Robot fully finished speaking. Keyboard hardware inputs physically enabled.")

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action == "ENTER": # Hardware mapping for Return/Enter
        input_enabled = False
        voice_manager.stop()
        if media_player:
            media_player.stop()
        print("[Explain Screen] Student pressed ENTER. Logging failure and advancing...")
        
        # 1. Log the Failure Interaction natively
        task_data = state_manager.get_current_task()
        task_id = task_data.get("task_id", "unknown") if task_data else "unknown"
        student_id = state_manager.get_current_student() or "unknown"
        
        log_data = {
            "student_id": student_id,
            "task_id": task_id,
            "result": "incorrect",
            "affordance_level_reached": state_manager.get_affordance_level(),
            "path_taken": ["evaluate_L1", "elaborate", "evaluate_L2", "explain"]
        }
        
        if not hasattr(state_manager, 'session_logs'):
            state_manager.session_logs = []
        state_manager.session_logs.append(log_data)
        
        try:
            from core import firebase
            firebase.log_event(log_data)
        except ImportError:
            pass
            
        print(f"[Explain Screen] LOGGED FAILURE: {log_data}")
        
        # 2. Rip into Evaluation Sequence natively
        print("[Explain Screen] Advancing sequence natively via FlowController...")
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.advance_cascade(parent_stack)
        except ImportError: pass
