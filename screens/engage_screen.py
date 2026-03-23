import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.voice_manager import VoiceManager

current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
ui_path = os.path.join(project_root, "ui", "engageUI.ui")

window = None
input_enabled = False
engage_data = {}
voice_manager = VoiceManager()

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
    print("[Engage Screen] Becoming active...")
    state_manager.set_current_screen("engage")
    
    task_data = state_manager.get_current_task()
    if not task_data or "engage" not in task_data:
        print("Error: No valid engage task found in state_manager.")
        window.title_label.setText("Error: Task not loaded.")
        return
        
    global input_enabled, engage_data
    input_enabled = False
    engage_data = task_data.get("engage", {})
    
    # 1. Populate Title
    window.title_label.setText(engage_data.get("task_title", "Let's Try Again!"))
    
    # 2. Populate Media (Prior Knowledge Recall)
    media_url = engage_data.get("video_url", "")
    if media_url:
        abs_media_path = os.path.join(project_root, media_url)
        if os.path.exists(abs_media_path):
            pixmap = QPixmap(abs_media_path)
            window.media_label.setPixmap(pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            window.media_label.setText("🌟\n[Media File Missing]")
    else:
        window.media_label.setText("🌟\n[No Visual Prompt Provided]")
        
    # 3. Multi-Stage Warm Emotional Speech Loop
    speech_start = engage_data.get("speech_start", "Let's review this together!")
    
    window.robot_text_label.setText(f"🤖 \"{speech_start}\"")
    print(f"🤖 ROBOT SPEAKS [EXTRA WARM & GENTLE TONE]: \"{speech_start}\"")
    voice_manager.speak(speech_start, f"engage_start_{task_data.get('task_id', 'id')}")
    
    # Extra slow, soothing computational cadence (1.8 words per second)
    words_count = len(speech_start.split())
    delay_ms = max(2500, int((words_count / 1.8) * 1000))
    QTimer.singleShot(delay_ms, play_second_speech)

def play_second_speech():
    global engage_data
    speech_end = engage_data.get("speech_end", "Press Enter when you're ready to try one more time!")
    
    if speech_end:
        window.robot_text_label.setText(f"🤖 \"{speech_end}\"")
        print(f"🤖 ROBOT SPEAKS [EXTRA WARM & GENTLE TONE]: \"{speech_end}\"")
        voice_manager.speak(speech_end, f"engage_end_{engage_data.get('task_id', 'id')}")
        words_count = len(speech_end.split())
        delay_ms = max(2500, int((words_count / 1.8) * 1000))
        QTimer.singleShot(delay_ms, enable_input)
    else:
        enable_input()

def enable_input():
    global input_enabled
    input_enabled = True
    window.robot_text_label.setText("🤖 Waiting for you to feel ready...")
    print("[Engage Screen] Robot fully finished speaking. Keyboard hardware inputs physically enabled.")
    # Step 49: Bind keyboard handler
    keyboard_manager.register_handler(handle_key_press)

def handle_key_press(action):
    global input_enabled
    if not input_enabled:
        return
        
    if action == "ENTER":
        input_enabled = False
        print("[Engage Screen] Student pressed ENTER. Entering absolute final Evaluation loop! (Level 3)")
        
        try:
            from core.navigator import navigator
            navigator.navigate_to("evaluate")
        except Exception as e:
            print(f"Warning: Could not transition back to Evaluate Screen. {e}")
