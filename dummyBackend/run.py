#!/usr/bin/env python3
"""
🤖 Akshi Robot — Dummy Backend Launcher
========================================
Launches BOTH the dummy robot and dummy analysis server together.

  • dummy_robot.py  → WebSocket server on ws://0.0.0.0:8765
  • dummy_server.py → Connects to the robot, sends fake metrics

Usage:
    python dummyBackend/run.py

This replaces BOTH:
    akshi-the-robot/maincopy.py   (spawned by core/backend_manager.py)
    server/server.py              (the remote analysis server)
"""

import asyncio
import subprocess
import sys
import os
import signal
import time

DUMMY_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DUMMY_DIR)

ROBOT_SCRIPT = os.path.join(DUMMY_DIR, "dummy_robot.py")
SERVER_SCRIPT = os.path.join(DUMMY_DIR, "dummy_server.py")

# Also import firebase helper to push IP
sys.path.insert(0, DUMMY_DIR)


def main():
    print("=" * 60)
    print("  🤖 AKSHI ROBOT — DUMMY BACKEND")
    print("  ─────────────────────────────────")
    print(f"  Robot:  dummy_robot.py  → ws://localhost:8765")
    print(f"  Server: dummy_server.py → connects to robot")
    print(f"  Press Ctrl+C to stop both")
    print("=" * 60)

    # Push IP to Firebase (optional)
    try:
        from dummy_firebase import update_connected_ip
        update_connected_ip()
    except Exception as e:
        print(f"[Run] Firebase IP push skipped: {e}")

    python = sys.executable

    # Start the dummy robot first
    robot_proc = subprocess.Popen(
        [python, ROBOT_SCRIPT],
        cwd=PROJECT_ROOT,
    )
    print(f"[Run] 🤖 Robot daemon started (PID: {robot_proc.pid})")

    # Wait a moment for the WebSocket server to be ready
    time.sleep(1.5)

    # Start the dummy server (connects to the robot)
    server_proc = subprocess.Popen(
        [python, SERVER_SCRIPT],
        cwd=PROJECT_ROOT,
    )
    print(f"[Run] 📊 Analysis server started (PID: {server_proc.pid})")

    # Handle graceful shutdown
    def cleanup(signum=None, frame=None):
        print("\n[Run] Shutting down...")
        for proc in [server_proc, robot_proc]:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("[Run] ✅ All processes stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Wait for either process to exit
    try:
        while True:
            if robot_proc.poll() is not None:
                print(f"[Run] ⚠️  Robot process exited (code {robot_proc.returncode})")
                cleanup()
            if server_proc.poll() is not None:
                print(f"[Run] ⚠️  Server process exited (code {server_proc.returncode})")
                cleanup()
            time.sleep(0.5)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
