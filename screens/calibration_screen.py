"""
Calibration Screen — "Akshi's Magical Eyes" Edition
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
from components.calibration_game import CalibrationGameWidget

window = None
state_timer = None
STATE_FILE = "akshi-the-robot/calibration_state.json"
COMMAND_FILE = "akshi-the-robot/calibration_command.json"
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
        voice_manager.speak(intro_msg, "calib_magic_intro")

        # 2. Tell the server to start tracking (same IPC as before)
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

        # 3. Start polling for server signals
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

            # ─── ACT 1: OWL EYES (Eyes Open) ───
            if status.startswith("Keep eyes OPEN"):
                self.game.set_phase("open")
                self.game.update_progress(current_frame, total_frames)

                if self.prompt_state != "open":
                    self.prompt_state = "open"
                    voice_manager.stop()
                    voice_manager.speak(
                        "Wow! Can you make your eyes BIG like a magical owl? "
                        "Look! Stars are appearing in the sky!",
                        "owl_eyes"
                    )

            # ─── ACT 2: SLEEPING BUNNY (Eyes Closed) ───
            elif status.startswith("Keep eyes CLOSED"):
                self.game.set_phase("closed")
                self.game.update_progress(current_frame, total_frames)

                if self.prompt_state != "closed":
                    self.prompt_state = "closed"
                    voice_manager.stop()
                    voice_manager.speak(
                        "Amazing! Now the owl is sleepy! "
                        "Can you close your eyes like a cozy sleeping bunny? "
                        "Shhh... the moon is rising!",
                        "sleeping_bunny"
                    )

            # ─── ACT 3: CELEBRATION (Done) ───
            elif status.startswith("DONE"):
                self.game.set_phase("done")

                if self.prompt_state != "done":
                    self.prompt_state = "done"
                    voice_manager.stop()
                    voice_manager.speak(
                        "WOW! You did it! Your magical eyes are fully charged! "
                        "You're AMAZING! Let's go learn something super cool!",
                        "super_power"
                    )

                    state_timer.stop()
                    keyboard_manager.unregister_handler()

                    # Delay to let the celebration play + voice finish
                    QTimer.singleShot(5000, self.proceed_to_task)

            print("[Calibration Game]", status)

        except Exception:
            pass

    def handle_key_press(self, mapped_action):
        if mapped_action == "SKIP":
            print("[Calibration Override] Manual skip via SKIP key.")
            if state_timer:
                state_timer.stop()
            keyboard_manager.unregister_handler()
            voice_manager.stop()
            try:
                with open(COMMAND_FILE, "w") as f:
                    json.dump({"type": "end_session"}, f)
            except:
                pass
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
