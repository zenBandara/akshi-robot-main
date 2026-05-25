# Akshi Robot: WebSocket & Video Streaming Architecture

This document serves as a comprehensive guide for developers working with or building on top of the existing legacy codebase for the Akshi robot. The backend (running on the robot) acts as a WebSocket server that handles physical face tracking, video streaming, and session orchestration. 

Any new frontend/analytics client must strictly adhere to the WebSocket protocols and JSON data structures defined below to ensure compatibility.

---

## 1. System Overview

The system is divided into two primary responsibilities:

1. **Local Face Tracking (Hardware/Backend):** Handled primarily in `maincopy.py`. The Raspberry Pi uses `Picamera2` and Google's `mediapipe` to detect a face in real-time. It then calculates the error (distance from the center of the frame) and physically moves servos (Yaw and Pitch) using `pigpio` to keep the user in the frame.
2. **Video Streaming & Analytics Orchestration (Network/WebSocket):** Handled in `web_socket.py`. The backend hosts a WebSocket server that streams compressed JPEG frames to a connected client and coordinates analytics sessions via JSON messages. 

---

## 2. WebSocket Server Connection Details

* **Protocol:** WebSocket (`ws://`)
* **Host:** `0.0.0.0` (Binds to the Pi's local IP address)
* **Port:** `8765`
* **Max Payload Size:** `5,000,000` bytes

When a client connects to the WebSocket server, the backend launches three concurrent asynchronous tasks to handle the connection:
1. `sender()`: Streams video frames to the client.
2. `listener()`: Listens for incoming analytics data from the client.
3. `session_controller()`: Manages the mock flow of students and tasks.

---

## 3. Video Streaming Protocol (Server -> Client)

The backend continuously captures frames, processes them, compresses them to JPEG, and sends them over the WebSocket as raw binary data.

### 3.1 Backend Processing (Legacy Code Context)
Before transmission, the backend applies a slight Gaussian blur and contrast adjustment to the frame. It compresses the image using `cv2.IMWRITE_JPEG_QUALITY` set to `60` to save bandwidth.

```python
# snippet from web_socket.py - sender() task
frame = self.latest_frame.copy()
frame = cv2.flip(frame, 1)

frame = cv2.GaussianBlur(frame, (0, 0), 1)
frame = cv2.addWeighted(frame, 1.5, frame, -0.5, 0)

ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
```

### 3.2 The Transmission Format
To ensure the client knows exactly where a frame begins and ends, the server uses a **length-prefixed binary format**. 

1. **Header (4 bytes):** An unsigned 32-bit integer (Big Endian) representing the total byte size of the upcoming image.
2. **Payload (N bytes):** The raw JPEG bytes.

```python
# snippet from web_socket.py - sender() task
data = buffer.tobytes()

# 1. Send the size of the payload (4 bytes, Big Endian)
await websocket.send(struct.pack(">I", len(data)))
# 2. Send the actual JPEG data
await websocket.send(data)
```

### 3.3 How the Client Should Receive the Video
The frontend developer must parse this binary stream. When the client receives a message:
* If it's `4 bytes` long, store it as the expected length of the next frame.
* The immediate next message will be the JPEG blob. The client can create an `ObjectURL` or decode it directly into an HTML `<img src="...">` or `<canvas>`.

---

## 4. Session Management (Server -> Client)

The backend acts as the orchestrator. It tells the frontend *when* a student starts a session and *when* it ends. Currently, this is mocked in the `session_controller()` using a predefined list of students (`["Nimal", "Kamal", "Saman", "Sunil"]`) and tasks (`["t_01", "t_02"]`).

### 4.1 Start Session
When a new student is ready, the server sends a JSON string:

```json
{
    "type": "start_session",
    "student_name": "Nimal",
    "task_id": "t_02"
}
```
**Client Responsibility:** Upon receiving this message, the frontend should initialize its analytics engine, clear previous metrics, and begin analyzing the incoming video stream for the specified student and task.

### 4.2 End Session
After a predetermined time (currently hardcoded to 60 seconds), the server will close the session by sending:

```json
{
    "type": "end_session"
}
```
**Client Responsibility:** Upon receiving this message, the frontend should halt its analytics and prepare the final metrics to be sent back to the backend or saved to a database.

---

## 5. Analytics Data (Client -> Server)

While the frontend runs the analytics, it needs to send data (metrics, statuses, etc.) back to the robot. The robot's backend constantly listens for incoming JSON strings.

### 5.1 Backend Listener
The backend simply awaits incoming messages, attempts to parse them as JSON, and stores them in `self.last_client_data`.

```python
# snippet from web_socket.py - listener() task
msg = await websocket.recv()
try:
    data = json.loads(msg)
    self.last_client_data = data
    print("Received metrics:", data)
except:
    print("Received raw message:", msg)
```

### 5.2 Expected Client Output
The frontend developer should send stringified JSON objects over the WebSocket. While the structure is flexible (the Python backend just parses it as a generic dictionary), a recommended format to maintain clarity is:

```json
{
    "type": "analytics_update",
    "student_name": "Nimal",
    "metrics": {
        "attention_score": 85.5,
        "emotion": "focused"
    },
    "timestamp": 1684930291
}
```

---

## 6. Summary of Developer Responsibilities

If you are building the new client/frontend, your system must:
1. Connect to `ws://<ROBOT_IP>:8765`.
2. Handle interleaved message types:
   * **Binary Messages:** Buffer 4-byte length headers and the subsequent JPEG payloads to render the live feed.
   * **Text (JSON) Messages:** Listen for `{"type": "start_session", ...}` and `{"type": "end_session"}` to control the lifecycle of your analytics engine.
3. Send text (JSON) messages back to the server with calculated metrics, which the robot can use to alter its behavior or save to a unified database.