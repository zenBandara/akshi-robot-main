import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, Qt, QUrl
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPainterPath, QRegion
from core.state_manager import state_manager
from core.voice_manager import VoiceManager
from core.keyboard_manager import keyboard_manager
from components.robot_eyes import get_robot_eyes

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "kinestaticUI.ui")

window = None
voice_manager = VoiceManager()
input_enabled = False
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

def setup_video(kinesthetic_data):
    global media_player, audio_output, video_widget
    
    media_url = kinesthetic_data.get("video_url", "")
    abs_media_path = os.path.join(project_root, media_url) if media_url else ""
    
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
    
    # Beautiful styling for the kinesthetic screen container
    container.setStyleSheet("background-color: #E8F5E9; border-radius: 20px;") # Soft green kinesthetic tone
    QTimer.singleShot(100, lambda: apply_rounded_clip(container, 20))
    
    audio_output = QAudioOutput()
    audio_output.setVolume(0)
    
    media_player = QMediaPlayer()
    media_player.setAudioOutput(audio_output)
    media_player.setVideoOutput(video_widget)
    
    if os.path.exists(abs_media_path):
        media_player.setSource(QUrl.fromLocalFile(abs_media_path))
        media_player.setLoops(QMediaPlayer.Infinite)
        media_player.play()
        print(f"[Kinesthetic Screen] Video playing: {abs_media_path}")
    else:
        print(f"[Kinesthetic Screen] Video file not found: {abs_media_path}")


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
    
    # Initialize UI video player
    setup_video(kinesthetic_data)
    
    # 1. Start dialogue sequence generically
    speech_start = kinesthetic_data.get("speech_start", "")
    speech_step_1 = kinesthetic_data.get("speech_step_1", "")
    speech_step_2 = kinesthetic_data.get("speech_step_2", "")
    speech_end = kinesthetic_data.get("speech_end", "")
    
    get_robot_eyes().set_expression("thinking")
    
    def step_4():
        get_robot_eyes().set_expression("default")
        if speech_end:
            window.robot_text_label.setText(f"🤖 \"{speech_end}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_end}\"")
            voice_manager.speak(speech_end, f"kin_{student_name}_end")
        enable_input()
        
    def step_3():
        get_robot_eyes().set_expression("surprised")
        if speech_step_2:
            window.robot_text_label.setText(f"🤖 \"{speech_step_2}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_step_2}\"")
            delay = voice_manager.speak(speech_step_2, f"kin_{student_name}_step2")
            QTimer.singleShot(delay + 600, step_4)
        else:
            step_4()
            
    def step_2():
        get_robot_eyes().set_expression("encouraging")
        if speech_step_1:
            window.robot_text_label.setText(f"🤖 \"{speech_step_1}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_step_1}\"")
            delay = voice_manager.speak(speech_step_1, f"kin_{student_name}_step1")
            QTimer.singleShot(delay + 600, step_3)
        else:
            step_3()

    if speech_start:
        window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
        print(f"🤖 ROBOT SPEAKS: \"{speech_start}\"")
        delay_1 = voice_manager.speak(speech_start, f"kin_{student_name}_start")
        QTimer.singleShot(delay_1 + 600, step_2)
    else:
        step_2()

def enable_input():
    global input_enabled
    print("Waiting for Teacher Intervention (P to Pass, F to Fail)...")
    input_enabled = True
    keyboard_manager.register_handler(handle_key_press)

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    action_upper = action.upper()
    
    if action_upper == "P":
        # Passed
        input_enabled = False
        voice_manager.stop()
        if media_player:
            media_player.stop()
        print("[Kinesthetic Screen] Teacher initiated PASS. Transitioning...")
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.on_correct_answer(parent_stack)
        except ImportError: pass
            
    elif action_upper == "F":
        # Failed
        input_enabled = False
        voice_manager.stop()
        if media_player:
            media_player.stop()
        print("[Kinesthetic Screen] Teacher initiated FAIL. Transitioning to Engage...")
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.on_kinesthetic_fail(parent_stack)
        except ImportError: pass