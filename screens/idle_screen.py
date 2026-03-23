import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QPropertyAnimation, Qt, QUrl
from PySide6.QtWidgets import QGraphicsOpacityEffect, QVBoxLayout
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from core.keyboard_manager import keyboard_manager
from core.state_manager import state_manager
from core.navigator import navigator

window = None
pulse_anim = None
fade_effect = None
media_player = None
video_widget = None

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
        
        # Deploy QMediaPlayer pipeline gracefully
        if media_player is None:
            setup_video()
        else:
            media_player.play()

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
    global window, media_player, video_widget
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    video_path = os.path.join(project_root, "assets", "video", "idle.mp4")
    
    # Instantiate raw hardware-accelerated invisible video bounding box
    video_widget = QVideoWidget()
    
    # Mathematically force PySide6 to scale the internal white video background completely outwards,
    # stretching it beyond the window edges identically to CSS 'background-size: cover'
    # This physically eradicates all black letterbox bars natively!
    video_widget.setAspectRatioMode(Qt.KeepAspectRatioByExpanding)
    
    # Dynamically mount directly into the centralized Web Container GUI layout frame
    layout = QVBoxLayout(window.web_container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(video_widget)
    
    # Compile Audio node and forcibly bypass hardware speaker channels
    audio_output = QAudioOutput()
    audio_output.setVolume(0)
    
    # Sync video rendering logic across an infinite loop
    media_player = QMediaPlayer()
    media_player.setAudioOutput(audio_output)
    media_player.setVideoOutput(video_widget)
    media_player.setSource(QUrl.fromLocalFile(video_path))
    media_player.setLoops(QMediaPlayer.Infinite)
    
    # Force auto-playback
    media_player.play()

def handle_key_press(mapped_action):
    global media_player
    if mapped_action == "WAKE":
        print("[Idle Screen] WAKE command triggered! Transitioning natively to Greeting...")
        if media_player is not None:
            media_player.pause()
        navigator.navigate_to("greeting")
