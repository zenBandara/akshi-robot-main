# WebSocket Architecture — Ginglu Robot

This document explains how the WebSocket communication system works in the Ginglu Robot project. It covers the connection setup, data flow, session lifecycle, and the IPC bridge between the frontend UI and the backend hardware tracker.

---

## 1. The Big Picture

The Ginglu Robot runs **two completely separate Python processes** on the same Raspberry Pi:

| Process | Entry File | Responsibility |
|---------|-----------|----------------|
| **Frontend** | `main.py` | PySide6 GUI — screens, navigation, voice, keyboard |
| **Backend** | `ginglu-the-robot/maincopy.py` | Camera, face tracking, servo motors, WebSocket server |

These two processes **cannot share variables** directly because they run in isolated memory spaces. They communicate using two mechanisms:

1. **JSON files on disk** (IPC) — for commands between Frontend ↔ Backend
2. **WebSocket** — for streaming data between Backend ↔ External Dashboard

```
┌──────────────┐    JSON Files     ┌──────────────┐    WebSocket     ┌──────────────┐
│   Frontend   │ ◄──────────────► │   Backend    │ ◄─────────────► │  Dashboard   │
│  (main.py)   │   (IPC Bridge)   │ (maincopy.py)│   (Port 8765)   │  (Browser)   │
└──────────────┘                   └──────────────┘                  └──────────────┘
```

---

## 2. How the Connection is Established

### Step 1: Backend Publishes Its IP to Firebase

When `maincopy.py` starts, it imports `web_socket.py`, which immediately calls:

```python
# File: ginglu-the-robot/web_socket.py (line 11)
fr.update_connected_ip()
```

This function (defined in `ginglu-the-robot/firebase_request.py`) detects the Raspberry Pi's local network IP address and writes it to Firebase Realtime Database:

```python
# File: ginglu-the-robot/firebase_request.py
def update_connected_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]  # e.g. "10.10.6.152"
    s.close()
    db.reference("connected_ip").set(ip)
```

After this runs, Firebase stores: `connected_ip: "10.10.6.152"`

### Step 2: Backend Opens a WebSocket Server

In `maincopy.py`, the WebSocket server is created and started on port **8765**:

```python
# File: ginglu-the-robot/maincopy.py (lines 172-173)
ws = WebSocketServer()
ws.start()
```

The `start()` method spins up a background thread that listens for incoming WebSocket connections on `0.0.0.0:8765` (accepts connections from any device on the network):

```python
# File: ginglu-the-robot/web_socket.py (lines 123-126)
async with websockets.serve(self.stream, "0.0.0.0", 8765, max_size=5_000_000):
    print("Server started")
    await asyncio.Future()  # Run forever
```

### Step 3: Dashboard Connects

The external dashboard (running on a laptop/phone browser) reads the IP from Firebase, then connects to:

```
ws://10.10.6.152:8765
```

Once connected, the `stream()` method fires and three parallel async tasks begin running.

---

## 3. The Three Async Tasks

When a dashboard client connects, three concurrent tasks run simultaneously inside `web_socket.py`:

### 3.1 Sender — Camera Frames → Dashboard

Sends live camera frames to the dashboard at ~20 FPS.

```python
# File: ginglu-the-robot/web_socket.py (lines 36-66)
async def sender():
    frame = self.latest_frame.copy()
    # Process: flip, blur, sharpen
    ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    data = buffer.tobytes()

    # Send frame size (4 bytes, big-endian) then the JPEG bytes
    await websocket.send(struct.pack(">I", len(data)))
    await websocket.send(data)
    await asyncio.sleep(0.05)  # ~20 FPS
```

**Data format:**
1. First message: 4 bytes (`>I` = unsigned int, big-endian) representing the JPEG size
2. Second message: Raw JPEG binary data

The `latest_frame` is continuously updated by `maincopy.py`'s main tracking loop:

```python
# File: ginglu-the-robot/maincopy.py (line 202)
ws.update_frame(frame)
```

### 3.2 Listener — Dashboard → Backend

Receives JSON messages sent back from the dashboard (e.g., calibration metrics, attention scores):

```python
# File: ginglu-the-robot/web_socket.py (lines 68-83)
async def listener():
    msg = await websocket.recv()
    data = json.loads(msg)
    self.last_client_data = data

    # Also write to disk so the Frontend UI can read it
    with open("calibration_state.json", "w") as f:
        json.dump(data, f)
```

The dashboard can send any JSON object. Common examples:

```json
{ "calibration_status": "Keep eyes OPEN (79/200)" }
{ "calibration_status": "Keep eyes CLOSED (150/200)" }
{ "calibration_status": "DONE" }
```

### 3.3 IPC Controller — Frontend → Backend → Dashboard

This is the bridge between the PySide6 frontend and the WebSocket. It polls a JSON file on disk every 50ms:

```python
# File: ginglu-the-robot/web_socket.py (lines 87-103)
async def ipc_controller():
    last_command = None
    while True:
        with open("calibration_command.json", "r") as f:
            cmd = json.load(f)

        if cmd and cmd != last_command:
            last_command = cmd
            await websocket.send(json.dumps(cmd))  # Forward to dashboard
        await asyncio.sleep(0.05)
```

**How a command travels from the UI to the dashboard:**

```
Frontend Screen                    Disk File                     IPC Controller              Dashboard
      │                                │                               │                        │
      │── writes JSON ──────────────►  │  calibration_command.json     │                        │
      │                                │                               │                        │
      │                                │ ◄── polls every 50ms ────────│                        │
      │                                │                               │                        │
      │                                │    detects new command ──────►│                        │
      │                                │                               │── websocket.send() ──►│
```

---

## 4. The IPC File System (Frontend ↔ Backend)

Since the Frontend (`main.py`) and Backend (`maincopy.py`) are separate processes, they use two JSON files inside `ginglu-the-robot/` as a shared mailbox:

| File | Direction | Purpose |
|------|-----------|---------|
| `calibration_command.json` | Frontend → Backend | Commands from the UI (start/end session) |
| `calibration_state.json` | Backend → Frontend | Status updates from the dashboard |

### Writing a command (Frontend side)

```python
# File: screens/calibration_screen.py (lines 52-57)
with open(COMMAND_FILE, "w") as f:
    json.dump({
        "type": "start_session",
        "student_name": student_name,
        "task_id": "face_calibration"
    }, f)
```

### Reading the state (Frontend side)

```python
# File: screens/calibration_screen.py (lines 77-78)
with open(STATE_FILE, "r") as f:
    data = json.load(f)
    status = data.get("calibration_status", "Not started yet")
```

---

## 5. Session Lifecycle (Student Sessions)

Each student has their own session. The session tells the dashboard "I am now tracking THIS student" and "I am done with this student."

### 5.1 Session Start

**When:** A student presses ENTER on the Student Call screen and arrives at the Calibration screen.

**Where:** `screens/calibration_screen.py` → `on_show()`

**What happens:**
1. `backend_manager.start()` launches `maincopy.py` as a subprocess
2. `maincopy.py` boots the camera, servos, and WebSocket server
3. The calibration screen writes a `start_session` command to the IPC file

```python
# Written to: ginglu-the-robot/calibration_command.json
{
    "type": "start_session",
    "student_name": "Kamal",
    "task_id": "face_calibration"
}
```

4. The `ipc_controller()` detects this and sends it over WebSocket to the dashboard
5. The dashboard now knows to start recording metrics for "Kamal"

### 5.2 During Session

While the student is active (Evaluate → Engage → Explore → etc.):
- The **sender** continuously streams camera frames to the dashboard
- The **listener** receives calibration/attention data back from the dashboard
- The **calibration_state.json** file keeps the Frontend UI updated with the latest status
- The face tracking loop in `maincopy.py` controls the robot's servos

### 5.3 Session End

**When:** The student finishes (celebration complete) OR moves to the next student.

**Where:** `core/session_logic.py` → `next_student()`

**What happens:**
1. An `end_session` command is written to the IPC file

```python
# Written to: ginglu-the-robot/calibration_command.json
{ "type": "end_session" }
```

2. The `ipc_controller()` detects this and sends it over WebSocket to the dashboard
3. The dashboard saves the student's final metrics
4. `backend_manager.stop()` terminates the `maincopy.py` subprocess
5. The camera is released, servos stop

### 5.4 Next Student

When the next student arrives:
- The flow returns to the Student Call screen
- The student presses ENTER → Calibration screen
- `backend_manager.start()` launches a **fresh** `maincopy.py` process
- A new `start_session` is sent with the new student's name
- The cycle repeats

### Visual Timeline

```
Student 1                          Student 2                          End
────────────────────────────────   ────────────────────────────────   ─────
│ start_session("Kamal")           │ start_session("Saman")          │
│ ► camera ON                      │ ► camera ON                     │
│ ► face tracking active           │ ► face tracking active          │
│ ► frames streaming               │ ► frames streaming              │
│ ► calibration → evaluate → ...   │ ► calibration → evaluate → ... │
│ end_session                      │ end_session                     │
│ ► camera OFF                     │ ► camera OFF                    │
│ ► subprocess killed              │ ► subprocess killed             │
```

---

## 6. Data Formats Summary

### Commands (Frontend → Dashboard via IPC)

| Command | JSON Payload | Trigger Point |
|---------|-------------|---------------|
| Start Session | `{"type": "start_session", "student_name": "...", "task_id": "..."}` | `calibration_screen.py` on_show() |
| End Session | `{"type": "end_session"}` | `session_logic.py` next_student() |

### Status Updates (Dashboard → Frontend via WebSocket)

| Status | JSON Payload | Meaning |
|--------|-------------|---------|
| Eyes Open | `{"calibration_status": "Keep eyes OPEN (79/200)"}` | Dashboard is collecting open-eye data |
| Eyes Closed | `{"calibration_status": "Keep eyes CLOSED (150/200)"}` | Dashboard is collecting closed-eye data |
| Done | `{"calibration_status": "DONE"}` | Calibration complete |

### Video Frames (Backend → Dashboard via WebSocket)

| Message | Format | Description |
|---------|--------|-------------|
| Frame size | 4 bytes, big-endian unsigned int | Length of the upcoming JPEG |
| Frame data | Raw binary JPEG | Compressed camera frame (quality=60) |

---

## 7. Key Files Reference

| File | Location | Role |
|------|----------|------|
| `web_socket.py` | `ginglu-the-robot/` | WebSocket server with sender, listener, and IPC controller |
| `firebase_request.py` | `ginglu-the-robot/` | Publishes the Pi's IP address to Firebase |
| `maincopy.py` | `ginglu-the-robot/` | Main backend loop — camera, face detection, servos, starts WebSocket |
| `calibration_command.json` | `ginglu-the-robot/` | IPC mailbox: Frontend writes commands here |
| `calibration_state.json` | `ginglu-the-robot/` | IPC mailbox: Dashboard status written here |
| `calibration_screen.py` | `screens/` | Writes `start_session`, reads calibration state |
| `session_logic.py` | `core/` | Writes `end_session`, stops backend subprocess |
| `backend_manager.py` | `core/` | Starts/stops the `maincopy.py` subprocess on demand |

---

## 8. Important Notes

- The WebSocket server runs on port **8765**. The dashboard must connect to `ws://<pi-ip>:8765`.
- The IP is auto-detected and pushed to Firebase every time the backend starts. The dashboard reads it from Firebase path `connected_ip`.
- The IPC polling interval is **50ms** — fast enough to feel instant during calibration transitions.
- Each student gets a **completely fresh** backend process. This ensures the camera is cleanly released and recalibrated for each child.
- The `serviceAccountKey.json` file must be present in `ginglu-the-robot/` for the Firebase IP upload to work.
