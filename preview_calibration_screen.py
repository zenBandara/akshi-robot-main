import sys
import json
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer


def main():
    app = QApplication(sys.argv)

    # Import after QApplication to match the main app's expectations.
    from screens.calibration_screen import get_ui

    w = get_ui()
    w.setWindowTitle("Preview: Calibration Screen")
    w.resize(1280, 720)
    w.show()

    if hasattr(w, "on_show"):
        QTimer.singleShot(0, w.on_show)

    # Simulate backend calibration status updates so the preview shows
    # stars/progress and transitions (open -> closed -> done).
    state_file = os.path.join("ginglu-the-robot", "calibration_state.json")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)

    total = 200
    tick = {"n": 0, "started": False}

    def write_status():
        # The real backend only counts frames when tracking is unpaused (clock enabled).
        if getattr(w.game, "_clock_enabled", False):
            n = tick["n"]
            tick["n"] += 2  # advance faster than real-time for preview

            if n <= total // 2:
                status = f"Keep eyes OPEN ({n}/{total})"
            elif n < total:
                status = f"Keep eyes CLOSED ({n}/{total})"
            else:
                status = "DONE"

            try:
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump({"calibration_status": status}, f)
            except Exception:
                pass

            if status == "DONE":
                sim_timer.stop()

    sim_timer = QTimer()
    sim_timer.timeout.connect(write_status)
    sim_timer.start(60)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
