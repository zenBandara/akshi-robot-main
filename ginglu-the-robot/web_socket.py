import asyncio
import websockets
import cv2
import struct
import threading
import json
import firebase_request as fr
import os
import queue
import time

# Set IP to Firebase
fr.update_connected_ip()


class WebSocketServer:

    def __init__(self):
        self.state_file = "calibration_state.json"
        self.command_file = "calibration_command.json"
        
        # Ensure json files exist
        if not os.path.exists(self.command_file):
            with open(self.command_file, "w") as f:
                json.dump({}, f)
        if not os.path.exists(self.state_file):
            with open(self.state_file, "w") as f:
                json.dump({"calibration_status": "Not started yet", "face_visible": True}, f)

        self.latest_frame = None
        self.last_client_data = {"calibration_status": "Not started yet", "face_visible": True}
        self.tracking_active = False  # Toggled by start_session/end_session IPC commands
        
        # NEW: Async state-writing queue to prevent blocking the frame loops
        self.state_queue = queue.Queue()
        self.state_lock = threading.Lock()
        self.write_thread = threading.Thread(target=self._state_writer_worker, daemon=True)
        self.write_thread.start()

    def _state_writer_worker(self):
        """Background thread that writes state to disk only when it changes."""
        last_written_data = None
        while True:
            try:
                # Wait for new data to write
                data = self.state_queue.get()
                if data is None: break
                
                # Only write if the data is different from what's already on disk
                if data != last_written_data:
                    try:
                        with open(self.state_file, "w") as f:
                            json.dump(data, f)
                        last_written_data = data.copy()
                    except Exception as e:
                        print(f"[WebSocket] State write error: {e}")
                
                self.state_queue.task_done()
            except Exception:
                time.sleep(0.01)

    def set_face_visible(self, visible):
        """Update the face visibility status in the shared state file."""
        with self.state_lock:
            if self.last_client_data.get("face_visible") == visible:
                return # Skip if no change
            
            self.last_client_data["face_visible"] = visible
            # Push to the async writer
            self.state_queue.put(self.last_client_data.copy())

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

                    # On Pi, deep copies of high-res frames in a loop can be slow. 
                    # Use a fast resize or direct encode if possible, but keeping original logic mostly intact.
                    frame = self.latest_frame
                    
                    if not self.tracking_active:
                        # Optimization: don't even process if inactive, just send tiny black frame
                        data = b"\x00" * 100 # Dummy small data
                    else:
                        frame = cv2.flip(frame, 1)
                        # GAUSSIAN BLUR is very expensive on a Pi CPU! 
                        # frame = cv2.GaussianBlur(frame, (0, 0), 1)
                        # Use a faster blur or skip it if lag is severe
                        
                        ret, buffer = cv2.imencode(
                            ".jpg",
                            frame,
                            [cv2.IMWRITE_JPEG_QUALITY, 50] # Lower quality slightly for speed
                        )
                        if not ret: continue
                        data = buffer.tobytes()

                    await websocket.send(struct.pack(">I", len(data)))
                    await websocket.send(data)

                    await asyncio.sleep(0.06) # Throttle slightly for Pi stability

            except websockets.exceptions.ConnectionClosed:
                print("Sender stopped")

        async def listener():
            try:
                while True:
                    msg = await websocket.recv()
                    try:
                        data = json.loads(msg)
                        with self.state_lock:
                            # Preserve face_visible state maintained by the local robot process
                            if "face_visible" in self.last_client_data:
                                data["face_visible"] = self.last_client_data["face_visible"]
                            
                            self.last_client_data = data
                            # Async write to disk
                            self.state_queue.put(data.copy())
                        
                    except:
                        pass

            except websockets.exceptions.ConnectionClosed:
                print("Listener stopped")

        async def ipc_controller():
            last_command = None
            while True:
                try:
                    if os.path.exists(self.command_file):
                        with open(self.command_file, "r") as f:
                            cmd = json.load(f)
                    else:
                        cmd = {}
                    
                    if cmd and cmd != last_command:
                        last_command = cmd
                        await websocket.send(json.dumps(cmd))
                        
                        with self.state_lock:
                            new_state = {"type": cmd.get("type", "unknown")}
                            if "face_visible" in self.last_client_data:
                                new_state["face_visible"] = self.last_client_data["face_visible"]
                            
                            self.last_client_data = new_state
                            self.state_queue.put(new_state.copy())
                        
                        # Toggle tracking based on student session commands
                        cmd_type = cmd.get("type")
                        if cmd_type in ["start_session", "resume_frames"]:
                            self.tracking_active = True
                            print(f"[WebSocket] Tracking ON ({cmd_type})")
                        elif cmd_type in ["end_session", "pause_frames"]:
                            self.tracking_active = False
                            print(f"[WebSocket] Tracking OFF ({cmd_type})")
                except Exception:
                    pass
                await asyncio.sleep(0.1) # Less frequent check for Pi CPU relief


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