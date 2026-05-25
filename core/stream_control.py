from __future__ import annotations

from core.ipc_queue import append_ipc_command


COMMAND_FILE = "ginglu-the-robot/calibration_command.json"


def set_frame_streaming(enabled: bool, *, reason: str | None = None) -> None:
    """Control whether the robot streams real frames or black frames.

    The robot-side websocket server treats:
    - {"type": "resume_frames"} as tracking_active=True (real frames)
    - {"type": "pause_frames"}  as tracking_active=False (black frames)
    """
    cmd = {"type": "resume_frames" if enabled else "pause_frames"}
    if reason:
        cmd["reason"] = str(reason)
    append_ipc_command(cmd, COMMAND_FILE)
