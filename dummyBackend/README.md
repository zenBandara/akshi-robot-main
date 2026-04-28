# 🤖 Akshi Robot — Dummy Backend

Replaces **both** hardware-dependent components so you can develop the
PySide6 frontend on your MacBook without the robot or the analysis server.

## Architecture

```
┌──────────────────────┐     JSON IPC files      ┌──────────────────────────┐
│  Frontend UI         │◄──calibration_state.json──│  dummy_robot.py          │
│  (python main.py)    │──calibration_command.json─►│  (replaces maincopy.py)  │
└──────────────────────┘                          │                          │
                                                  │  WebSocket :8765         │
                                                  └─────────┬────────────────┘
                                                            │
                                                  ┌─────────▼────────────────┐
                                                  │  dummy_server.py         │
                                                  │  (replaces server.py)    │
                                                  │  Fakes attention metrics │
                                                  └──────────────────────────┘
```

## Quick Start

```bash
# Terminal 1 — Start the dummy robot + analysis server
pyenv activate akshi
cd /path/to/akshi-robot-main
python dummyBackend/run.py

# Terminal 2 — Start the frontend UI (unchanged)
pyenv activate akshi
cd /path/to/akshi-robot-main
python main.py
```

## What each file does

| File | Replaces | Purpose |
|---|---|---|
| `dummy_robot.py` | `akshi-the-robot/maincopy.py` | Fake camera + WebSocket server on `:8765`. Streams synthetic frames, reads IPC JSON commands, responds to the analysis server. |
| `dummy_server.py` | `server/server.py` | Connects to the dummy robot, receives frames, sends fake attention metrics + calibration status back. |
| `dummy_firebase.py` | `akshi-the-robot/firebase_request.py` + `server/firebase_operations.py` | Uses real Firebase credentials (if present) or gracefully degrades. |
| `run.py` | — | Single entry point that launches both dummy_robot and dummy_server together. |
