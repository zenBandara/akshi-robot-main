"""
Backend Process Manager
Manages the lifecycle of the backend face-tracking subprocess.
Start it when a student sits down, stop it when switching students.
"""
import subprocess
import sys
import os
import signal

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Toggle this to switch between dummy and real robot
USE_DUMMY = True
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_process = None

def start():
    """Start the backend face-tracking subprocess if not already running."""
    global _process
    if _process is not None and _process.poll() is None:
        print("[Backend Manager] Process already running, skipping start.")
        return
    
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if USE_DUMMY:
        print("[Backend Manager] Starting DUMMY backend subprocess...")
        _process = subprocess.Popen(
            [sys.executable, os.path.join(_project_root, "dummyBackend", "run.py")],
            cwd=_project_root,
        )
        print(f"[Backend Manager] Dummy backend started (PID: {_process.pid})")
    else:
        cores = os.cpu_count() or 1
        command = []
        
        if sys.platform.startswith("linux") and cores >= 4:
            print("[Backend Manager] Quad-core detected. Starting REAL backend on CPU Cores 2 & 3...")
            command.extend(["taskset", "-c", "2,3"])
        else:
            print(f"[Backend Manager] {cores} cores detected. Starting REAL backend without core binding...")
            
        command.extend([sys.executable, os.path.join(_project_root, "akshi-the-robot", "maincopy.py")])
        
        _process = subprocess.Popen(
            command,
            cwd=os.path.join(_project_root, "akshi-the-robot"),
        )
        print(f"[Backend Manager] Real backend started (PID: {_process.pid})")

def stop():
    """Stop the backend face-tracking subprocess if running."""
    global _process
    if _process is None:
        return
    if _process.poll() is not None:
        print("[Backend Manager] Process already exited.")
        _process = None
        return
    
    print(f"[Backend Manager] Stopping face-tracking subprocess (PID: {_process.pid})...")
    _process.terminate()
    try:
        _process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print("[Backend Manager] Force killing subprocess...")
        _process.kill()
        _process.wait()
    _process = None
    print("[Backend Manager] Subprocess stopped.")

def is_running():
    """Check if the backend process is currently alive."""
    return _process is not None and _process.poll() is None
