import subprocess
import os
import sys

_backend_process = None

def start_backend():
    global _backend_process
    if _backend_process is None:
        print("Starting background tracking process securely...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _backend_process = subprocess.Popen(
            [sys.executable, "maincopy.py"],
            cwd=os.path.join(project_root, "akshi-the-robot"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

def stop_backend():
    global _backend_process
    if _backend_process is not None:
        print("Shutting down background tracking process to free camera...")
        try:
            _backend_process.terminate()
            _backend_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _backend_process.kill()
        finally:
            _backend_process = None
