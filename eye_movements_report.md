# Physical Robot Eyes Integration Report

## 1. Overview of the Problem & Solution
Previously, there was a structural disconnect between the digital user interface (PySide6 application) and the physical robot hardware (ESP32). When the main application triggered an eye change (e.g., `get_robot_eyes().set_expression("encouraging")`), it only updated the digital ASCII art on the tablet screen. The physical robot eyes remained static because the Serial Port (`/dev/ttyACM0`) was exclusively locked by the face-tracking subprocess (`maincopy.py`).

**The Solution:** 
We implemented an **Inter-Process Communication (IPC)** bridge. Instead of the main application trying to open a conflicting Serial connection, it now writes a command to our shared `calibration_command.json` mailbox. The `maincopy.py` subprocess continuously listens to this mailbox and executes the physical hardware commands safely on behalf of the main application.

---

## 2. Technical Architecture

### A. Main Application (`components/robot_eyes.py`)
When a screen requests an emotion change, the `RobotEyesWidget` maps the digital state to a hardware state and appends a JSON IPC command:
```json
{"type": "set_eye_expression", "expression": "cheer", "id": "uuid", "ts": 1234567890}
```

### B. WebSocket Server (`web_socket.py`)
The WebSocket server running inside the subprocess reads the incoming IPC commands. If it detects a `set_eye_expression` command, it triggers a newly added `on_eye_command` callback.

### C. Subprocess Hardware (`maincopy.py`)
The `maincopy.py` script intercepts the callback and uses the `EyeController` class to send the exact byte commands (`H`, `S`, `C`, `L`) to the ESP32 over the Serial connection.

---

## 3. Comprehensive Emotion Mapping

We have successfully mapped the existing UI states to the new physical states provided by the `EyeController`. Here is the exact mapping that is now active across the robot:

| UI State (PySide6) | Physical State (ESP32) | Serial Command | Primary Use Cases |
| :--- | :--- | :---: | :--- |
| **`default`** | **`happy`** | `'H'` | Idle, resting state, waiting for student input. |
| **`sad`** | **`sad`** | `'S'` | Teacher intervention needed, face tracker lost, incorrect answers. |
| **`encouraging`** | **`cheer`** | `'C'` | Positive reinforcement, task completions, celebrations. |
| **`surprised`** | **`lovely`** | `'L'` | Greeting the student, saying goodbye, special moments. |
| **`thinking`** | **`happy`** *(fallback)* | `'H'` | Used when the robot is calculating; defaults to a positive baseline. |
| **`sleeping`** | **`happy`** *(fallback)* | `'H'` | Used during standby modes. |

---

## 4. Face Tracker Synchronization
A major design consideration was ensuring that the automated face tracker (`mediapipe`) inside `maincopy.py` did not conflict with the UI-driven emotion changes. 

**How they work together flawlessly:**
The face tracking logic strictly uses an edge-triggered state machine (`last_face_state`). It only ever sends a physical eye command at the exact moment a face is **lost** (sends `sad`) or **found** (sends `happy`). While a face remains steadily tracked in the frame, the tracker sends no eye commands. This allows the main application to inject `cheer` or `lovely` commands during gameplay, and those emotions will properly persist without the tracker constantly overriding them back to `happy`.