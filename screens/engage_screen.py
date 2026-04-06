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
ui_path = os.path.join(project_root, "ui", "engageUI.ui")

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

def setup_video(engage_data):
    global media_player, audio_output, video_widget
    
    media_url = engage_data.get("video_url", "")
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
    
    # Yellow engage styling matching the XML template
    container.setStyleSheet("background-color: #FFECB3; border-radius: 20px; border: 4px solid #FFCA28;") 
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
        print(f"[Engage Screen] Video playing: {abs_media_path}")
    else:
        print(f"[Engage Screen] Video file not found: {abs_media_path}")


def on_show():
    global input_enabled
    print("[Engage Screen] Becoming active...")
    state_manager.set_current_screen("engage")
    
    task_data = state_manager.get_current_task()
    if not task_data or "engage" not in task_data:
        print("Error: No valid engage task found in state_manager.")
        window.title_label.setText("Error: Task not loaded.")
        return
        
    engage_data = task_data.get("engage", {})
    student_name = str(state_manager.get_current_student() or "friend").capitalize()
    
    input_enabled = False
    voice_manager.stop()
    
    window.title_label.setText(engage_data.get("task_title", "Let's Try Again!"))
    
    # Boot the video Engine
    setup_video(engage_data)
        
    # 3. Multi-Stage Warm Emotional Speech Loop mapped sequentially
    speech_start = engage_data.get("speech_start", "Let's try something super fun safely together.")
    speech_middle = engage_data.get("speech_middle", "Watch our character carefully on the screen!")
    speech_end = engage_data.get("speech_end", "Press the Enter key when you are all done!")
    
    get_robot_eyes().set_expression("encouraging")
    
    def complete_engage():
        get_robot_eyes().set_expression("default")
        if speech_end:
            window.robot_text_label.setText(f"🤖 \"{speech_end}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_end}\"")
            voice_manager.speak(speech_end, f"engage_{student_name}_end")
        enable_input()
        
    def play_middle():
        get_robot_eyes().set_expression("thinking")
        if speech_middle:
            window.robot_text_label.setText(f"🤖 \"{speech_middle}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_middle}\"")
            delay = voice_manager.speak(speech_middle, f"engage_{student_name}_mid")
            QTimer.singleShot(delay + 600, complete_engage)
        else:
            complete_engage()
            
    if speech_start:
        window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
        print(f"🤖 ROBOT SPEAKS: \"{speech_start}\"")
        start_delay = voice_manager.speak(speech_start, f"engage_{student_name}_start")
        QTimer.singleShot(start_delay + 600, play_middle)
    else:
        play_middle()

def enable_input():
    global input_enabled
    input_enabled = True
    print("[Engage Screen] Robot fully finished speaking. Keyboard hardware inputs physically enabled.")
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
            
        print("[Engage Screen] Student pressed ENTER. Entering absolute final Evaluation loop! (Level 3)")
        
        from core.flow_controller import flow_controller
        flow_controller.cascade_index = 8
        state_manager.current_stage = "evaluate_L3"
        state_manager.set_affordance_level(3)
        
        try:
            from core.navigator import navigator
            navigator.navigate_to("evaluate")
        except Exception as e:
            print(f"Warning: Could not transition back to Evaluate Screen. {e}")
