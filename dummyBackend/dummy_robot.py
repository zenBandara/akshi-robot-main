"""
Dummy Robot Daemon — replaces ginglu-the-robot/maincopy.py

What it does:
  1. Generates synthetic camera frames (animated gradient + fake face marker)
  2. Runs a WebSocket server on 0.0.0.0:8765 (same port as real robot)
  3. Streams JPEG frames using the exact same wire protocol:
       → 4-byte big-endian length prefix
       → raw JPEG bytes
  4. Reads IPC commands from calibration_command.json (written by the UI)
  5. Receives metrics JSON from the analysis server and writes to calibration_state.json
  6. Pushes the local IP to Firebase (optional)

No hardware dependencies — no pigpio, picamera2, serial, or RPi.GPIO.
"""

import asyncio
import websockets
import struct
import json
import os
import time
import math
import numpy as np
import cv2
from pathlib import Path

# ── IPC file paths (relative to ginglu-the-robot/, same as real code) ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROBOT_DIR = os.path.join(PROJECT_ROOT, "ginglu-the-robot")
COMMAND_FILE = os.path.join(ROBOT_DIR, "calibration_command.json")
STATE_FILE = os.path.join(ROBOT_DIR, "calibration_state.json")


def ensure_ipc_files():
    """Create the JSON IPC files if they don't exist."""
    os.makedirs(ROBOT_DIR, exist_ok=True)
    if not os.path.exists(COMMAND_FILE):
        with open(COMMAND_FILE, "w") as f:
            json.dump({}, f)
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"calibration_status": "Not started yet"}, f)


def generate_frame(frame_num: int) -> bytes:
    """
    Generate a synthetic 640×480 JPEG frame with:
      - Animated gradient background
      - Bouncing circle simulating a face detection target
      - Timestamp overlay
    """
    w, h = 640, 480
    frame = np.zeros((h, w, 3), dtype=np.uint8)

    # Animated gradient background
    t = frame_num * 0.02
    for y in range(h):
        r = int(30 + 20 * math.sin(t + y * 0.01))
        g = int(40 + 15 * math.cos(t * 0.7 + y * 0.015))
        b = int(60 + 25 * math.sin(t * 1.3 + y * 0.008))
        frame[y, :] = (b, g, r)

    # Bouncing face-like circle
    cx = int(w / 2 + 120 * math.sin(t * 0.5))
    cy = int(h / 2 + 60 * math.cos(t * 0.3))
    cv2.circle(frame, (cx, cy), 50, (100, 200, 255), 3)
    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

    # Simple face features inside the circle
    cv2.circle(frame, (cx - 15, cy - 10), 5, (255, 255, 255), -1)  # left eye
    cv2.circle(frame, (cx + 15, cy - 10), 5, (255, 255, 255), -1)  # right eye
    cv2.ellipse(frame, (cx, cy + 12), (12, 6), 0, 0, 180, (255, 255, 255), 2)  # smile

    # Timestamp
    ts = time.strftime("%H:%M:%S")
    cv2.putText(frame, f"DUMMY ROBOT | {ts}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(frame, "No hardware required", (10, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

    # Encode as JPEG
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return buf.tobytes()


class DummyWebSocketServer:
    """
    Drop-in replacement for ginglu-the-robot/web_socket.py WebSocketServer.
    Same wire protocol, same IPC JSON bridge.
    """

    def __init__(self):
        ensure_ipc_files()
        self.last_client_data = None
        self.tracking_active = False
        self.frame_num = 0

    async def stream(self, websocket):
        print("[DummyRobot] Client connected")

        async def sender():
            """Stream synthetic JPEG frames at ~20 FPS."""
            try:
                while True:
                    jpeg_data = generate_frame(self.frame_num)
                    self.frame_num += 1

                    # Same wire format as real robot: 4-byte length + JPEG
                    await websocket.send(struct.pack(">I", len(jpeg_data)))
                    await websocket.send(jpeg_data)

                    await asyncio.sleep(0.05)  # ~20 FPS
            except websockets.exceptions.ConnectionClosed:
                print("[DummyRobot] Sender stopped — client disconnected")

        async def listener():
            """Receive metrics JSON from the analysis server."""
            try:
                while True:
                    msg = await websocket.recv()
                    try:
                        data = json.loads(msg)
                        self.last_client_data = data

                        # Write to calibration_state.json (same as real robot)
                        with open(STATE_FILE, "w") as f:
                            json.dump(data, f)

                        # Only log meaningful events, not every metrics tick
                        msg_type = data.get("type", "")
                        cal_status = data.get("calibration_status", "")
                        if msg_type != "metrics":
                            print(f"[DummyRobot] Received: {data}")
                        elif cal_status and cal_status != getattr(self, '_last_cal_status', ''):
                            self._last_cal_status = cal_status
                            print(f"[DummyRobot] Calibration: {cal_status}")
                    except (json.JSONDecodeError, TypeError):
                        print(f"[DummyRobot] Received raw message: {msg[:80]}")
            except websockets.exceptions.ConnectionClosed:
                print("[DummyRobot] Listener stopped — client disconnected")

        async def ipc_controller():
            """Read JSONL calibration_command.json and forward commands to the server."""
            last_pos = 0
            while True:
                try:
                    path = Path(COMMAND_FILE)
                    if not path.exists():
                        await asyncio.sleep(0.05)
                        continue

                    with path.open("r", encoding="utf-8") as f:
                        f.seek(last_pos)
                        lines = f.readlines()
                        last_pos = f.tell()

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            cmd = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        await websocket.send(json.dumps(cmd))

                        self.last_client_data = {"type": cmd.get("type", "unknown")}
                        with open(STATE_FILE, "w") as f:
                            json.dump(self.last_client_data, f)

                        # Toggle tracking state
                        if cmd.get("type") == "start_session":
                            self.tracking_active = True
                            print(f"[DummyRobot] ▶ Session STARTED for {cmd.get('student_name', '?')}")
                        elif cmd.get("type") == "end_session":
                            self.tracking_active = False
                            print("[DummyRobot] ⏹ Session ENDED")

                        print(f"[DummyRobot] → Forwarded IPC command: {cmd.get('type')}")
                except Exception:
                    pass
                await asyncio.sleep(0.05)

        # Run all three tasks concurrently
        tasks = [
            asyncio.create_task(sender()),
            asyncio.create_task(listener()),
            asyncio.create_task(ipc_controller()),
        ]

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for task in pending:
            task.cancel()

        print("[DummyRobot] Client disconnected")

    async def run(self):
        """Start the WebSocket server on port 8765."""
        async with websockets.serve(
            self.stream,
            "0.0.0.0",
            8765,
            max_size=5_000_000
        ):
            print("[DummyRobot] 🤖 WebSocket server running on ws://0.0.0.0:8765")
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    print("=" * 50)
    print("  🤖 GINGLU DUMMY ROBOT DAEMON")
    print("  Replaces: ginglu-the-robot/maincopy.py")
    print("  WebSocket: ws://localhost:8765")
    print("=" * 50)

    server = DummyWebSocketServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n[DummyRobot] Stopped.")
