import os
import csv
import json
import threading
import queue
from datetime import datetime
from core.state_manager import state_manager

# File paths
CSV_FILE_PATH = "data/student_telemetry.csv"
STATE_FILE = "ginglu-the-robot/calibration_state.json"

class TelemetryLogger:
    """
    High-granularity CSV logger for research analysis.
    Captures every UI interaction, screen transition, and evaluation result.
    """
    def __init__(self):
        self.log_queue = queue.Queue()
        self.headers = [
            "timestamp", "session_id", "student_name", "task_id", 
            "event_type", "event_detail", "is_correct", 
            "current_phase", "current_state", "face_visible"
        ]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)
        
        # Initialize CSV with headers if it doesn't exist
        if not os.path.exists(CSV_FILE_PATH):
            with open(CSV_FILE_PATH, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)
        
        # Start background worker thread for non-blocking writes
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _get_face_visibility(self):
        """Reads real-time face visibility from the calibration state file."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    # Support both "face_visible" and "calibration_status" checks if needed
                    return data.get("face_visible", False)
        except Exception:
            pass
        return False

    def log_event(self, event_type, detail, is_correct=None):
        """
        Public API to log an event. 
        Automatically gathers context from state_manager and flow_controller.
        """
        # We import flow_controller inside to avoid circular dependencies
        from core.flow_controller import flow_controller
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Context gathering
        session_id = state_manager.get_current_session() or "SYSTEM_INIT"
        student_name = state_manager.get_current_student() or "SYSTEM"
        task = state_manager.get_current_task()
        task_id = task.get("task_id", "none") if task else "none"
        
        # Get phase and state from flow_controller
        current_phase = flow_controller.identified_phase or "none"
        current_state = flow_controller.progression_state or "IDENTIFYING"
        
        face_visible = self._get_face_visibility()
        
        row = [
            timestamp, session_id, student_name, task_id,
            event_type, detail, 
            str(is_correct) if is_correct is not None else "-",
            current_phase, current_state, str(face_visible)
        ]
        
        self.log_queue.put(row)

    def _worker(self):
        """Background thread that writes queued logs to disk."""
        while True:
            row = self.log_queue.get()
            if row is None:
                break
            try:
                with open(CSV_FILE_PATH, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
            except Exception as e:
                print(f"[TelemetryLogger] Write error: {e}")
            finally:
                self.log_queue.task_done()

# Singleton instance
telemetry_logger = TelemetryLogger()
