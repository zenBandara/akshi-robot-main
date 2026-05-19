import asyncio
import websockets
import cv2
import struct
import threading
import json
import firebase_request as fr
import os

# Set IP to Firebase
fr.update_connected_ip()


class WebSocketServer:

    def __init__(self):
        
        # Ensure json files exist
        if not os.path.exists("calibration_command.json"):
            with open("calibration_command.json", "w") as f:
                json.dump({}, f)
        if not os.path.exists("calibration_state.json"):
            with open("calibration_state.json", "w") as f:
                json.dump({"calibration_status": "Not started yet", "face_visible": True}, f)


        self.latest_frame = None
        self.last_client_data = {}  # store received data
        self.tracking_active = True  # Default to True for standalone testing; toggled by IPC commands

    def set_face_visible(self, visible):
        """Update the face visibility status in the shared state file."""
        if self.last_client_data is None:
            self.last_client_data = {}
        
        self.last_client_data["face_visible"] = visible
        print(f"[WebSocket] Updating face_visible to: {visible}")
        try:
            with open("calibration_state.json", "w") as f:
                json.dump(self.last_client_data, f)
        except Exception as e:
            print(f"[WebSocket] Error writing face_visible to JSON: {e}")

    def update_frame(self, frame):
        self.latest_frame = frame

    def _prepare_frame(self):
        """Process and encode the frame in a thread-safe way."""
        frame = self.latest_frame
        if frame is None:
            return None
            
        # Convert RGB (from maincopy.py) to BGR for OpenCV encoding
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        if not self.tracking_active:
            # Send pitch-black frames to keep connection alive
            frame[:] = 0
        else:
            # Combine operations
            frame = cv2.flip(frame, 1)
            # Apply sharpening (unsharp mask) - much faster at 640x360
            blurred = cv2.GaussianBlur(frame, (0, 0), 1)
            frame = cv2.addWeighted(frame, 1.5, blurred, -0.5, 0)

        ret, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 60]
        )
        return buffer.tobytes() if ret else None

    async def stream(self, websocket):
        print("Client connected")

        async def sender():
            try:
                while True:
                    # Run CPU-bound image processing in a thread
                    data = await asyncio.to_thread(self._prepare_frame)
                    
                    if data is None:
                        await asyncio.sleep(0.05)
                        continue

                    try:
                        await websocket.send(struct.pack(">I", len(data)))
                        await websocket.send(data)
                    except websockets.exceptions.ConnectionClosed:
                        break

                    await asyncio.sleep(0.05)

            except Exception as e:
                print(f"Sender error: {e}")
            print("Sender stopped")

        async def listener():
            try:
                while True:
                    msg = await websocket.recv()

                    try:
                        data = json.loads(msg)
                        # Merge local state with received metrics
                        if "face_visible" in self.last_client_data:
                            data["face_visible"] = self.last_client_data["face_visible"]
                        
                        self.last_client_data = data
                        with open("calibration_state.json", "w") as f:
                            json.dump(data, f)
                        print("Received metrics:", data)
                    except:
                        print("Received raw message:", msg)

            except websockets.exceptions.ConnectionClosed:
                print("Listener stopped")

        

        async def ipc_controller():
            last_command = None
            while True:
                try:
                    with open("calibration_command.json", "r") as f:
                        cmd = json.load(f)
                    
                    if cmd and cmd != last_command:
                        last_command = cmd
                        await websocket.send(json.dumps(cmd))
                        new_state = {"type": cmd.get("type", "unknown")}
                        if "face_visible" in self.last_client_data:
                            new_state["face_visible"] = self.last_client_data["face_visible"]
                            
                        self.last_client_data = new_state
                        with open("calibration_state.json", "w") as f:
                            json.dump(self.last_client_data, f)
                        
                        # Toggle tracking based on student session commands
                        cmd_type = cmd.get("type")
                        if cmd_type in ["start_session", "resume_frames"]:
                            self.tracking_active = True
                            print(f"[WebSocket] Tracking ON ({cmd_type})")
                        elif cmd_type in ["end_session", "pause_frames"]:
                            self.tracking_active = False
                            print(f"[WebSocket] Tracking OFF ({cmd_type})")
                        
                        print("Sent IPC command to server:", cmd)
                except Exception as e:
                    pass
                await asyncio.sleep(0.05)

        sender_task = asyncio.create_task(sender())
        listener_task = asyncio.create_task(listener())
        session_task = asyncio.create_task(ipc_controller())

        done, pending = await asyncio.wait(
            [sender_task, listener_task, session_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

        for task in pending:
            task.cancel()

        print("Client disconnected")


    def start(self):
        def run():
            async def main():
                async with websockets.serve(
                    self.stream,
                    "0.0.0.0",
                    8765,
                    max_size=5_000_000
                ):
                    print("Server started")
                    await asyncio.Future()

            asyncio.run(main())

        threading.Thread(target=run, daemon=True).start()