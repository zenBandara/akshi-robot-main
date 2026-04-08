import os
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator
from core.voice_manager import VoiceManager

window = None
state_timer = None
STATE_FILE = "akshi-the-robot/calibration_state.json"
COMMAND_FILE = "akshi-the-robot/calibration_command.json"
voice_manager = VoiceManager()

class CalibrationScreenUI(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel("Initializing Camera...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 48px; font-weight: bold; color: #333333;")
        self.layout.addWidget(self.label)
        
        self.setStyleSheet("background-color: #87CEEB;")
        self.last_status = ""
        self.prompt_state = ""

        if not os.path.exists(COMMAND_FILE):
            with open(COMMAND_FILE, "w") as f:
                json.dump({}, f)
        if not os.path.exists(STATE_FILE):
            with open(STATE_FILE, "w") as f:
                json.dump({"calibration_status": "Not started yet"}, f)

    def on_show(self):
        print("[Calibration Screen] Becoming active...")
        state_manager.set_current_screen("calibration")
        keyboard_manager.register_handler(self.handle_key_press)
        
        # Start backend face-tracking subprocess for this student
        from core import backend_manager
        backend_manager.start()
        
        student_name = state_manager.get_current_student() or "friend"
        self.prompt_state = "init"
        
        # 1. Playful Intro Prompt!
        intro_msg = f"Hi {student_name}! Before we play, let's test our robot eyes! Look right at my camera!"
        voice_manager.stop()
        voice_manager.speak(intro_msg, "calib_intro")
        
        # 2. Tell Dedicated Server to start tracking AND reset local state
        try:
            with open(COMMAND_FILE, "w") as f:
                json.dump({
                    "type": "start_session",
                    "student_name": student_name,
                    "task_id": "face_calibration"
                }, f)
            with open(STATE_FILE, "w") as f:
                json.dump({"calibration_status": "Not started yet"}, f)
        except Exception as e:
            print("[Calibration Error] Failed to write command file:", e)

        # 3. Start Polling for Remote Dedicated Server Signal
        global state_timer
        if state_timer is None:
            state_timer = QTimer(self)
            state_timer.timeout.connect(self.poll_state)
            
        self.last_status = "Initializing Camera..."
        self.label.setText(self.last_status)
        self.setStyleSheet("background-color: #87CEEB;")
            
        state_timer.start(100)

    def poll_state(self):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                
            status = data.get("calibration_status", "Not started yet")
            if status != self.last_status:
                self.last_status = status
                self.label.setText(status)
                
                # Check server status and prompt child playfully
                if status[:14] == "Keep eyes OPEN":
                    self.setStyleSheet("background-color: lightgreen;")
                    if self.prompt_state != "open":
                        self.prompt_state = "open"
                        voice_manager.stop()
                        voice_manager.speak("Can you keep your eyes wide open like a big owl?", "eyes_open")
                        
                elif status[:16] == "Keep eyes CLOSED":
                    self.setStyleSheet("background-color: orange;")
                    if self.prompt_state != "closed":
                        self.prompt_state = "closed"
                        voice_manager.stop()
                        voice_manager.speak("Great job! Now squeeze your eyes shut like you're sleeping!", "eyes_closed")
                        
                elif status[:4] == "DONE":
                    self.setStyleSheet("background-color: lightgray;")
                    if self.prompt_state != "done":
                        self.prompt_state = "done"
                        voice_manager.stop()
                        voice_manager.speak("Perfect! My robot sensors are fully calibrated! Let's get started!", "calib_done")
                    
                    state_timer.stop()
                    keyboard_manager.unregister_handler()
                    
                    # Small delay so voice finishes before jumping
                    QTimer.singleShot(4000, self.proceed_to_task)
                else:
                    self.setStyleSheet("background-color: #87CEEB;")
                
                print("[Calibration UI] Server signals:", status)
                 
        except Exception as e:
            pass

    def handle_key_press(self, mapped_action):
        if mapped_action == "SKIP":
            print("[Calibration Override] Manual skipped via SKIP key.")
            if state_timer: state_timer.stop()
            keyboard_manager.unregister_handler()
            voice_manager.stop()
            try:
                with open(COMMAND_FILE, "w") as f:
                    json.dump({"type": "end_session"}, f)
            except: pass
            self.proceed_to_task()

    def proceed_to_task(self):
        print("Calibration completed or skipped. Proceeding to task routing...")
        student_name = state_manager.get_current_student() or "friend"
        try:
            from core.flow_controller import flow_controller
            target_node = flow_controller.setup_dynamic_start(student_name)
            navigator.navigate_to(target_node)
        except Exception as e:
            navigator.navigate_to("evaluate")

def get_ui():
    global window
    if window is None:
        window = CalibrationScreenUI()
    return window

