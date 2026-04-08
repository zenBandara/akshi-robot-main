# Akshi Robot: Architecture & Communication Breakdown

This document provides a comprehensive explanation of how the Akshi Robot's software is structured, focusing on how the robot's local UI communicates with the local hardware script, and how that script communicates with your remote dedicated server.

## 1. High-Level Architecture
The system is divided into three distinct layers to ensure that heavy video processing and network streaming do not freeze the child-friendly UI.

1. **The Frontend Robot UI (`main.py`)**: A PySide6 graphical application that runs the interactive screens, plays robot audio, and tracks the student's progress through the lesson.
2. **The Local Background Daemon (`akshi-the-robot/maincopy.py`)**: A headless script running concurrently on the Robot's Raspberry Pi. It captures the camera feed, moves the physical neck servos using MediaPipe face tracking, and hosts a WebSocket server.
3. **The Remote Dedicated Server**: An external computer/server that connects to the Robot over WebSockets, receives the live camera feed, performs heavy remote computations (like evaluating eyes open/closed or attention metrics), and sends commands back to the Robot.

---

## 2. Process Lifecycle & Subprocessing

When you run `python main.py` from the root folder, here is exactly what happens:

1. **Subprocess Booting**: Inside `main.py`, Python uses the `subprocess` module to physically spawn a completely separate background Terminal process running `/akshi-the-robot/maincopy.py`. 
2. **Camera Initialization**: `maincopy.py` boots up the camera (`Picamera2`) and begins calculating face centroids using MediaPipe so the physical robot neck (`pigpio`) can track the face independently.
3. **WebSocket Server**: `maincopy.py` spins up a local server on port `8765` using `web_socket.py`.
4. **Firebase IP Registration**: `firebase_request.py` automatically figures out what local Wi-Fi IP address the robot is using and posts it to the Firebase Realtime Database. This allows your Remote Dedicated Server to know exactly what IP to connect to!

---

## 3. The Inter-Process Communication (IPC) Bridge
Because the Frontend UI and the Background Daemon are two separate processes, they cannot easily share variables in memory. We use local JSON files inside `akshi-the-robot/` to pass messages back and forth instantly.

* **`calibration_command.json`**: Written to by the Frontend UI. Read by the Background Daemon. This is used to issue commands like `"start_session"` or `"end_session"`.
* **`calibration_state.json`**: Written to by the Background Daemon. Read continuously by the Frontend UI. This provides live updates from the Remote Server (like `"Keep eyes OPEN"`).

---

## 4. The Calibration Flow: Step-By-Step
Here is the exact timeline of events when you invite a student:

1. **Transition to Calibration Screen**:
   When you press `ENTER` on the `student_call_screen.py`, the Robot immediately navigates to `screens/calibration_screen.py`.

2. **UI Initialization & Prompt**:
   `calibration_screen.py` turns blue and says `"Initializing Camera..."`. The robot speaks playfully: *"Hi [Student]! Before we play, let's test our robot eyes!"*

3. **Sending the Start Command**:
   While speaking, the UI writes the following to `calibration_command.json`:
   ```json
   {
       "type": "start_session",
       "student_name": "Nimal",
       "task_id": "face_calibration"
   }
   ```
   At the exact same time, it writes `{"calibration_status": "Not started yet"}` into `calibration_state.json` to ensure a clean slate.

4. **Background Daemon Forwards to Server**:
   Inside `akshi-the-robot/web_socket.py`, a function named `ipc_controller()` polls that JSON file every 500ms. When it sees the `"start_session"` command, it intercepts it and **sends it completely unchanged over the WebSocket connection to your Remote Dedicated Server**.

---

## 5. Why the screen says "Not started yet"

If your UI is stuck showing the blue screen with `"Not started yet"`, it means **the UI successfully did its job and is currently waiting on your Remote Dedicated Server to respond.**

Here is what the Frontend is waiting for:

1. **The Remote Server Must Connect**: Your dedicated backend must use the IP found in Firebase to establish a WebSocket connection (`ws://<robot-ip>:8765`).
2. **The Remote Server Must Receive Video**: `web_socket.py` is actively streaming JPEG-encoded camera frames over that socket.
3. **The Remote Server Must Assess the Child**: The server uses its own proprietary logic to process the video stream.
4. **The Remote Server Must Send Commands**: When the server wants the UI to update, it must send a JSON string back through the WebSocket connection to the Robot. 

### The Expected Server Responses

**To start the open-eye test**, the Remote Dedicated Server must send:
```json
{"calibration_status": "Keep eyes OPEN"}
```
*What happens on the Robot:* `web_socket.py` receives this over the socket and dumps it into `calibration_state.json`. The PySide UI sees the file changed, turns the screen **GREEN**, and the Robot uses `VoiceManager` to playfully ask the child to open their eyes like an owl.

**To start the closed-eye test**, the Remote Dedicated Server must send:
```json
{"calibration_status": "Keep eyes CLOSED"}
```
*What happens on the Robot:* The PySide UI detects the change, turns the screen **ORANGE**, and asks the child to squeeze their eyes shut.

**To finish calibration**, the Remote Dedicated Server must send:
```json
{"calibration_status": "DONE"}
```
*What happens on the Robot:* The PySide UI detects the change, turns **GREY**, praises the child *"Perfect! My sensors are calibrated!"*, waits 4 seconds for the voice to finish, and **automatically routes the UI state to Level 1 Evaluation**.

---

### Summary Checklist for your Lecturer Evaluation
If you need to discuss this with your lecturer, emphasize the following robust architectural choices:
- We successfully **decoupled** the hardware/camera polling layer (`maincopy.py`) from the frontend Qt Event Loop (`main.py`) using subprocessing.
- We built a reliable **local JSON IPC Bridge** so the UI can dynamically query external hardware states without blocking animations or freezing.
- The UI is designed as a **reactive state machine**; it playfully responds to WebSocket commands emitted by the central Firebase-registered Dedicated Server, ensuring fluid 5E Matrix routing immediately upon the `"DONE"` signal.
