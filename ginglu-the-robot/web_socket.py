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
        self.tracking_active = False  # Toggled by start_session/end_session IPC commands

    def set_face_visible(self, visible):
        """Update the face visibility status in the shared state file."""
        if self.last_client_data is None:
            self.last_client_data = {}
        
        self.last_client_data["face_visible"] = visible
        try:
            with open("calibration_state.json", "w") as f:
                json.dump(self.last_client_data, f)
        except Exception as e:
            print(f"[WebSocket] Error writing face_visible to JSON: {e}")

    def update_frame(self, frame):
        self.latest_frame = frame

    async def stream(self, websocket):
        print("Client connected")

        async def sender():
            try:
                while True:
                    if self.latest_frame is None:
                        await asyncio.sleep(0.05)
                        continue

                    frame = self.latest_frame.copy()
                    
                    if not self.tracking_active:
                        # Send pitch-black frames to keep connection alive but prevent face detection
                        frame[:] = 0
                    else:
                        frame = cv2.flip(frame, 1)
                        frame = cv2.GaussianBlur(frame, (0, 0), 1)
                        frame = cv2.addWeighted(frame, 1.5, frame, -0.5, 0)

                    ret, buffer = cv2.imencode(
                        ".jpg",
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, 60]
                    )

                    if not ret:
                        continue

                    data = buffer.tobytes()

                    await websocket.send(struct.pack(">I", len(data)))
                    await websocket.send(data)

                    await asyncio.sleep(0.05)

            except websockets.exceptions.ConnectionClosed:
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
                        # We let state_writer handle the file writing
                    except:
                        print("Received raw message:", msg)

            except websockets.exceptions.ConnectionClosed:
                print("Listener stopped")

        async def state_writer():
            """Writes calibration_state.json at most 10 times a second if data changed."""
            last_written = None
            while True:
                try:
                    if self.last_client_data != last_written:
                        to_write = self.last_client_data.copy()
                        with open("calibration_state.json", "w") as f:
                            json.dump(to_write, f)
                        last_written = to_write
                except Exception as e:
                    pass
                await asyncio.sleep(0.1)

        async def ipc_controller():
            last_command = None
            last_mtime = 0
            while True:
                try:
                    mtime = os.path.getmtime("calibration_command.json")
                    if mtime != last_mtime:
                        try:
                            with open("calibration_command.json", "r") as f:
                                cmd = json.load(f)
                            # Only update last_mtime if parsing was successful
                            last_mtime = mtime
                        except json.JSONDecodeError:
                            # File is probably partially written; wait and try again next loop
                            await asyncio.sleep(0.01)
                            continue
                        
                        if cmd and cmd != last_command:
                            last_command = cmd
                            await websocket.send(json.dumps(cmd))
                            new_state = {"type": cmd.get("type", "unknown")}
                            if "face_visible" in self.last_client_data:
                                new_state["face_visible"] = self.last_client_data["face_visible"]
                                
                            self.last_client_data = new_state
                            
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
        writer_task = asyncio.create_task(state_writer())
        session_task = asyncio.create_task(ipc_controller())

        done, pending = await asyncio.wait(
            [sender_task, listener_task, writer_task, session_task],
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