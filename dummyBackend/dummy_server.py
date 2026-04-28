"""
Dummy Analysis Server — replaces server/server.py

What it does:
  1. Connects to the dummy robot's WebSocket at ws://localhost:8765
  2. Receives synthetic JPEG frames (but doesn't actually analyze them)
  3. Listens for session control messages (start_session / end_session)
  4. Simulates the full calibration flow:
       → "Keep eyes OPEN (N/200)" for ~100 frames
       → "Keep eyes CLOSED (N/200)" for ~100 frames
       → "DONE"
  5. After calibration, sends fake attention metrics at ~10 Hz:
       → overall, eye, face, emotion, calibration_status
  6. No heavy dependencies — no mediapipe, dlib, deepface, scipy, etc.

Wire protocol (matches real server exactly):
  Robot → Server:  4-byte big-endian length + JPEG bytes (binary frames)
                   OR JSON string (control messages)
  Server → Robot:  JSON string with metrics or calibration status
"""

import asyncio
import websockets
import struct
import json
import time
import math
import random


class DummyAttentionAnalyzer:
    """
    Simulates RealTimeAttentionAnalyzer from server.py
    Generates realistic-looking fake metrics.
    """

    def __init__(self):
        self.is_tracking = False
        self.calibration_status = "NIL"
        self.current_student = "unknown"
        self.current_task = "t_00"

        # Calibration state
        self.calibration_frame = 0
        self.calibration_total = 200
        self.is_calibrated = False

        # Metric generation
        self.start_time = 0
        self.base_attention = 75.0
        self.emotion_cycle = ["neutral", "happy", "neutral", "neutral", "surprise", "neutral"]
        self.emotion_index = 0

    def reset(self):
        """Reset all state for a new session."""
        self.calibration_frame = 0
        self.is_calibrated = False
        self.calibration_status = "Not started yet"
        self.start_time = time.time()
        self.base_attention = 70 + random.random() * 15
        self.emotion_index = 0

    def tick_calibration(self) -> dict:
        """
        Advance calibration by one frame.
        Returns a metrics dict to send to the robot.
        """
        self.calibration_frame += 1
        current = self.calibration_frame
        total = self.calibration_total

        if current <= total // 2:
            status = f"Keep eyes OPEN ({current}/{total})"
        elif current < total:
            status = f"Keep eyes CLOSED ({current}/{total})"
        else:
            status = "DONE"
            self.is_calibrated = True
            self.start_time = time.time()

        self.calibration_status = status

        return {
            "type": "metrics",
            "calibration_status": status,
            "overall": 0,
            "eye": 0,
            "face": 0,
            "emotion": "neutral",
            "timestamp": time.time()
        }

    def generate_metrics(self) -> dict:
        """
        Generate realistic-looking fake attention metrics.
        Uses sine waves with noise to simulate natural fluctuations.
        """
        elapsed = time.time() - self.start_time
        t = elapsed

        # Smooth sinusoidal attention with noise
        eye = self.base_attention + 10 * math.sin(t * 0.3) + random.gauss(0, 3)
        face = self.base_attention + 8 * math.cos(t * 0.2) + random.gauss(0, 4)
        overall = (eye * 0.5 + face * 0.5)

        # Clamp to valid range
        eye = max(0, min(100, eye))
        face = max(0, min(100, face))
        overall = max(0, min(100, overall))

        # Cycle through emotions every ~15 seconds
        if int(elapsed) % 15 == 0 and int(elapsed) > 0:
            self.emotion_index = (self.emotion_index + 1) % len(self.emotion_cycle)

        emotion = self.emotion_cycle[self.emotion_index]

        return {
            "type": "metrics",
            "calibration_status": self.calibration_status,
            "overall": round(overall, 2),
            "eye": round(eye, 2),
            "face": round(face, 2),
            "emotion": emotion,
            "timestamp": time.time()
        }


async def receiver(websocket, analyzer):
    """
    Receive data from the robot WebSocket:
      - JSON control messages (start_session, end_session)
      - Binary frames (4-byte length + JPEG) — consumed but not processed
    """
    print("[DummyServer] Receiver started")

    while True:
        try:
            msg = await websocket.recv()

            # Try JSON (control message)
            try:
                data = json.loads(msg)
                msg_type = data.get("type")

                if msg_type == "start_session":
                    student = data.get("student_name", "unknown")
                    task = data.get("task_id", "t_00")
                    analyzer.current_student = student
                    analyzer.current_task = task
                    analyzer.reset()
                    analyzer.is_tracking = True
                    print(f"[DummyServer] ▶ START SESSION: {student} | task: {task}")

                elif msg_type == "end_session":
                    analyzer.is_tracking = False
                    print("[DummyServer] ⏹ END SESSION")

                continue
            except (json.JSONDecodeError, TypeError):
                pass

            # Otherwise it's a binary frame — consume it
            try:
                size = struct.unpack(">I", msg)[0]
                frame_data = await websocket.recv()
                # Frame received and discarded (no real analysis)
            except struct.error:
                pass

        except websockets.exceptions.ConnectionClosed:
            print("[DummyServer] Connection closed by robot")
            break
        except Exception as e:
            print(f"[DummyServer] Receiver error: {e}")
            await asyncio.sleep(0.1)


async def sender(websocket, analyzer):
    """
    Send metrics/calibration status back to the robot at ~10-50 Hz.
    During calibration: advance one calibration frame per tick.
    After calibration: send fake attention metrics.
    """
    print("[DummyServer] Sender started")

    while True:
        try:
            if analyzer.is_tracking:
                if not analyzer.is_calibrated:
                    # Advance calibration (one frame per tick at ~10 Hz = ~20 sec total)
                    data = analyzer.tick_calibration()
                    await websocket.send(json.dumps(data))
                    await asyncio.sleep(0.1)
                else:
                    # Send fake attention metrics
                    data = analyzer.generate_metrics()
                    await websocket.send(json.dumps(data))
                    await asyncio.sleep(0.02)
            else:
                # Not tracking — idle wait
                await asyncio.sleep(0.5)

        except websockets.exceptions.ConnectionClosed:
            print("[DummyServer] Connection closed by robot")
            break
        except Exception as e:
            print(f"[DummyServer] Sender error: {e}")
            await asyncio.sleep(0.1)


async def connect_to_robot(uri: str):
    """Connect to the robot's WebSocket and run receiver + sender concurrently."""
    analyzer = DummyAttentionAnalyzer()

    while True:
        try:
            print(f"[DummyServer] Connecting to robot at {uri}...")
            async with websockets.connect(uri) as websocket:
                print(f"[DummyServer] ✅ Connected to robot!")

                await asyncio.gather(
                    receiver(websocket, analyzer),
                    sender(websocket, analyzer)
                )

        except (ConnectionRefusedError, OSError) as e:
            print(f"[DummyServer] Robot not ready ({e}). Retrying in 2s...")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[DummyServer] Connection lost: {e}. Reconnecting in 2s...")
            await asyncio.sleep(2)


async def main():
    uri = "ws://127.0.0.1:8765"
    await connect_to_robot(uri)


if __name__ == "__main__":
    print("=" * 50)
    print("  📊 AKSHI DUMMY ANALYSIS SERVER")
    print("  Replaces: server/server.py")
    print("  Connects to: ws://127.0.0.1:8765")
    print("=" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[DummyServer] Stopped.")
