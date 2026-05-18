"""
Calibration Screen — "Jinglu's Magical Eyes" Edition
====================================================
Replaces the plain colored-screen calibration with an animated 3-act mini-game.

The IPC bridge (calibration_command.json / calibration_state.json) is UNCHANGED —
same JSON protocol, just a drastically better visual experience.
"""

import os
import json
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator
from core.voice_manager import VoiceManager
from components.robot_eyes import get_robot_eyes
from components.calibration_game import CalibrationGameWidget

window = None
state_timer = None
STATE_FILE = "ginglu-the-robot/calibration_state.json"
COMMAND_FILE = "ginglu-the-robot/calibration_command.json"
voice_manager = VoiceManager()

# Regex to extract frame counts from status like "Keep eyes OPEN (47/200)"
_PROGRESS_RE = re.compile(r"\((\d+)/(\d+)\)")


class CalibrationScreenUI(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # The animated game widget
        self.game = CalibrationGameWidget()
        self.main_layout.addWidget(self.game)

        self.last_status = ""
        self.prompt_state = ""

        if not os.path.exists(COMMAND_FILE):
            with open(COMMAND_FILE, "w") as f:
                json.dump({}, f)
        if not os.path.exists(STATE_FILE):
            with open(STATE_FILE, "w") as f:
                json.dump({"calibration_status": "Not started yet"}, f)

    def on_show(self):
        print("[Calibration Screen] 🎮 Magical Eyes game starting...")
        state_manager.set_current_screen("calibration")
        keyboard_manager.register_handler(self.handle_key_press)
        get_robot_eyes().set_expression("encouraging")

        student_name = state_manager.get_current_student() or "friend"
        self.prompt_state = "init"

        # Reset the game visuals
        self.game.reset()
        self.game.set_phase("init")

        # 1. Magical Intro Prompt!
        intro_msg = (
            f"Hi {student_name}! We're going to play a magical eyes game! "
            f"Can you look right at my camera?"
        )
        voice_manager.stop()
        delay_ms = voice_manager.speak(intro_msg, "calib_magic_intro")

        # Clear any existing state
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({"calibration_status": "Not started yet"}, f)
        except: pass

        # Start Open Eyes Phase strictly AFTER the intro finishes + buffer
        QTimer.singleShot(delay_ms + 1000, self.prompt_open_eyes)

    def prompt_open_eyes(self):
        if self.prompt_state == "done": return # Aborted
        
        self.game.set_phase("open")
        self.prompt_state = "open"
        get_robot_eyes().set_expression("surprised")
        delay_ms = voice_manager.speak(
            "Wow! Can you make your eyes BIG like a magical owl? Look! Stars are appearing in the sky!",
            "owl_eyes"
        )
        
        # Start backend tracking ONLY AFTER the instructions are fully spoken
        QTimer.singleShot(delay_ms + 500, self.begin_backend_tracking)

    def begin_backend_tracking(self):
        student_name = state_manager.get_current_student() or "friend"
        try:
            with open(COMMAND_FILE, "w") as f:
                json.dump({"type": "start_session", "student_name": student_name, "task_id": "face_calibration"}, f)
        except Exception as e:
            print("[Calibration Error] Failed to write command file:", e)

        # Start polling for authentic server signals
        global state_timer
        if state_timer is None:
            state_timer = QTimer(self)
            state_timer.timeout.connect(self.poll_state)

        self.last_status = "Not started yet"
        state_timer.start(100)

    def poll_state(self):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)

            status = data.get("calibration_status", "Not started yet")
            if status == self.last_status:
                return

            self.last_status = status

            # Extract progress numbers if present
            match = _PROGRESS_RE.search(status)
            current_frame = int(match.group(1)) if match else 0
            total_frames = int(match.group(2)) if match else 200

            # Update visuals from authentic backend data
            if status.startswith("Keep eyes OPEN") or status.startswith("Keep eyes CLOSED"):
                self.game.update_progress(current_frame, total_frames)

            # ─── ACT 2: SLEEPING BUNNY (Eyes Closed) ───
            if status.startswith("Keep eyes CLOSED"):
                if self.prompt_state != "closed":
                    self.prompt_state = "closed"
                    
                    # 🛑 CRITICAL: Immediately pause the backend from counting frames while we speak!
                    try:
                        with open(COMMAND_FILE, "w") as f:
                            json.dump({"type": "pause_frames"}, f)
                    except: pass

                    self.game.set_phase("closed")
                    get_robot_eyes().set_expression("sleeping")
                    voice_manager.stop()
                    delay_ms = voice_manager.speak(
                        "Amazing! Now the owl is sleepy! Can you close your eyes like a cozy sleeping bunny? Shhh... the moon is rising!",
                        "sleeping_bunny"
                    )
                    
                    # Resume frames only after the student knows what to do
                    QTimer.singleShot(delay_ms + 500, self.resume_backend_tracking)

            # ─── ACT 3: CELEBRATION (Done) ───
            elif status.startswith("DONE"):
                if self.prompt_state != "done":
                    self.prompt_state = "done"
                    
                    try:
                        with open(COMMAND_FILE, "w") as f:
                            json.dump({"type": "pause_frames"}, f)
                    except: pass
                    
                    self.game.set_phase("done")
                    get_robot_eyes().set_expression("surprised")
                    
                    if state_timer:
                        state_timer.stop()
                        
                    voice_manager.stop()
                    delay_ms = voice_manager.speak(
                        "WOW! You did it! Your magical eyes are fully charged! You're AMAZING! Let's go learn something super cool!",
                        "super_power"
                    )

                    keyboard_manager.unregister_handler()
                    QTimer.singleShot(delay_ms + 1000, self.proceed_to_task)

            print("[Calibration Backend Status]", status)

        except Exception:
            pass

    def resume_backend_tracking(self):
        try:
            with open(COMMAND_FILE, "w") as f:
                json.dump({"type": "resume_frames"}, f)
        except: pass

    def handle_key_press(self, mapped_action):
        if mapped_action == "SKIP":
            print("[Calibration Override] Manual skip via SKIP key.")
            if state_timer:
                state_timer.stop()
            self.prompt_state = "done"
            keyboard_manager.unregister_handler()
            voice_manager.stop()
            try:
                with open(COMMAND_FILE, "w") as f:
                    json.dump({"type": "end_session"}, f)
            except:
                pass
            self.proceed_to_task()

    def proceed_to_task(self):
        get_robot_eyes().set_expression("default")
        print("Calibration completed or skipped. Starting adaptive question flow...")
        import core.session_logic as session_logic
        session_logic.start_student_questions()


def get_ui():
    global window
    if window is None:
        window = CalibrationScreenUI()
    return window
