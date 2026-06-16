import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer, QUrl
from PySide6.QtWidgets import QVBoxLayout, QLabel, QApplication
from PySide6.QtGui import QPainterPath, QRegion, QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes
from core.stream_control import set_frame_streaming

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "engageUI.ui")

window = None
input_enabled = False
voice_manager = VoiceManager()
video_label = None
frame_timer = None
timeout_timer = None
current_frames = []
current_frame_idx = 0
current_playing_dir = None

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

current_playing_dir = None

def swap_video(stage, engage_data):
    """Dynamically hot-swaps the underlying image sequence layer matching the vocal queue."""
    global current_frames, current_frame_idx, frame_timer, current_playing_dir
    
    urls_dict = engage_data.get("video_urls", {})
    media_url = urls_dict.get(stage, "")
    
    if not media_url:
        return
        
    base_dir = media_url.rsplit('.', 1)[0]
    abs_dir_path = os.path.join(project_root, base_dir)
    
    if os.path.isdir(abs_dir_path):
        if abs_dir_path == current_playing_dir:
            print(f"[Engage Screen] Continuing seamless sequence for stage '{stage}'...")
            return
            
        frames = [os.path.join(abs_dir_path, f) for f in os.listdir(abs_dir_path) if f.endswith('.jpg')]
        frames.sort()
        current_frames = frames
        current_frame_idx = 0
        current_playing_dir = abs_dir_path
        
        if current_frames and frame_timer:
            frame_timer.start(66) # 15 FPS (~66ms)
            print(f"[Engage Screen] Image sequence playing stage '{stage}': {abs_dir_path}")
    else:
        print(f"[Engage Screen] Image sequence dir not found for stage '{stage}': {abs_dir_path}")

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
    
    # Yellow engage styling matching the XML template
    container.setStyleSheet("background-color: #FFECB3; border-radius: 20px; border: 4px solid #FFCA28;") 
    QTimer.singleShot(100, lambda: apply_rounded_clip(container, 20))
    
    if frame_timer is None:
        frame_timer = QTimer()
        frame_timer.timeout.connect(update_frame)


def on_timeout():
    global input_enabled, timeout_timer, frame_timer
    if not input_enabled:
        return
    input_enabled = False
    voice_manager.stop()
    get_robot_eyes().set_expression("default")
    if frame_timer:
        frame_timer.stop()
    if timeout_timer:
        timeout_timer.stop()
        timeout_timer = None
    print("[Engage Screen] ⏰ 90s timeout — auto-advancing to next screen.")
    try:
        from core.flow_controller import flow_controller
        parent_stack = window.parentWidget()
        if parent_stack:
            flow_controller.advance_cascade(parent_stack)
    except ImportError: pass

def on_show():
    global input_enabled, timeout_timer
    if timeout_timer:
        timeout_timer.stop()
        timeout_timer = None
    print("[Engage Screen] Becoming active...")
    state_manager.set_current_screen("engage")

    try:
        set_frame_streaming(True, reason="engage")
    except Exception as e:
        print("[Engage Screen] Error resuming frames:", e)
    
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
    
    # Boot the video infrastructure completely muted
    setup_video_container()
        
    # 3. Multi-Stage Warm Emotional Speech Loop mapped sequentially
    speech_start = engage_data.get("speech_start", "Let's try something super fun safely together.")
    speech_middle = engage_data.get("speech_middle", "Watch our character carefully on the screen!")
    speech_end = engage_data.get("speech_end", "Say 'Okay' when you are all done!")
    audio_delay_ms = engage_data.get("audio_delay_ms", 0)
    
    get_robot_eyes().set_expression("default")
    
    def complete_engage():
        if not input_enabled: return
        swap_video("end", engage_data)
        get_robot_eyes().set_expression("default")
        if speech_end:
            window.robot_text_label.setText(f"🤖 \"{speech_end}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_end}\"")
            voice_manager.speak(speech_end, f"engage_{student_name}_end")
            
    def play_middle():
        if not input_enabled: return
        swap_video("step_1", engage_data)
        get_robot_eyes().set_expression("default")
        if speech_middle:
            window.robot_text_label.setText(f"🤖 \"{speech_middle}\"")
            print(f"🤖 ROBOT SPEAKS: \"{speech_middle}\"")
            delay = voice_manager.speak(speech_middle, f"engage_{student_name}_mid")
            QTimer.singleShot(delay + 600, complete_engage)
        else:
            complete_engage()
            
    if speech_start:
        swap_video("start", engage_data)
        window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
        window.update()
        QApplication.processEvents()
        
        print(f"🤖 ROBOT SPEAKS: \"{speech_start}\" (delayed {audio_delay_ms}ms for video sync)")
        # Delay audio so video frames start first — configurable via JSON
        def _play_start():
            delay = voice_manager.speak(speech_start, f"engage_{student_name}_start")
            QTimer.singleShot(delay + 600, play_middle)
        QTimer.singleShot(audio_delay_ms, _play_start)
    else:
        play_middle()
        
    print(f"[Engage Screen] Enabling keyboard input immediately to allow for speech interruption.")
    enable_input()
    
    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.setInterval(90000)
    timeout_timer.timeout.connect(on_timeout)
    timeout_timer.start()


def enable_input():
    global input_enabled
    input_enabled = True
    print("[Engage Screen] Robot fully finished speaking. Keyboard hardware inputs physically enabled.")
    keyboard_manager.register_handler(handle_key_press)


def handle_key_press(action):
    global input_enabled, timeout_timer
    if not input_enabled:
        return
        
    if action in ["ENTER", "YES"]:
        input_enabled = False
        voice_manager.stop()
        get_robot_eyes().set_expression("default")
        if frame_timer:
            frame_timer.stop()
        if timeout_timer:
            timeout_timer.stop()
            timeout_timer = None
            
        print("[Engage Screen] Student said OKAY/YES. Flowing smoothly toward Evaluate L2 natively.")
        try:
            from core.flow_controller import flow_controller
            parent_stack = window.parentWidget()
            if parent_stack:
                flow_controller.advance_cascade(parent_stack)
        except ImportError: pass
