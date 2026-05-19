import os
import csv
import datetime
import threading
from core.state_manager import state_manager

class TelemetryLogger:
    def __init__(self):
        self.log_dir = "logs"
        self.filename = os.path.join(self.log_dir, "telemetry.csv")
        self.lock = threading.Lock()
        
        self.headers = [
            "timestamp", "session_id", "student_name", "task_id", 
            "event_type", "event_detail", "is_correct", 
            "current_phase", "current_state", "affordance_level"
        ]
        
        # Ensure log directory exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Initialize CSV with headers if it doesn't exist
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_event(self, event_type, event_detail="-", is_correct="-", sync=False):
        """
        Logs an event to the CSV file. 
        Automatically gathers context from state_manager and flow_controller.
        """
        # Gather context
        timestamp = datetime.datetime.now().isoformat()
        session_id = state_manager.get_current_session() or "unknown"
        student_name = state_manager.get_current_student() or "unknown"
        current_task = state_manager.get_current_task()
        task_id = current_task.get("task_id", "unknown") if current_task else "unknown"
        affordance_level = state_manager.get_affordance_level()
        
        # We import flow_controller here to avoid circular dependency
        try:
            from core.flow_controller import flow_controller
            current_phase = flow_controller.identified_phase or "none"
            current_state = flow_controller.progression_state or "unknown"
        except ImportError:
            current_phase = "unknown"
            current_state = "unknown"

        row = [
            timestamp, session_id, student_name, task_id,
            event_type, event_detail, is_correct,
            current_phase, current_state, affordance_level
        ]

        if sync:
            self._write_row(row)
        else:
            # Write to CSV in a background thread to prevent UI lag
            threading.Thread(target=self._write_row, args=(row,), daemon=True).start()

    def _write_row(self, row):
        with self.lock:
            try:
                with open(self.filename, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
            except Exception as e:
                print(f"[TelemetryLogger] Error writing to CSV: {e}")

# Global singleton
telemetry_logger = TelemetryLogger()
