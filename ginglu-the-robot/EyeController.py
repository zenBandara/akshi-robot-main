import serial
import time
import threading
import queue

class EyeController:
    def __init__(self):
        self.port = '/dev/ttyACM0'
        self.baudrate = 115200
        self.timeout = 1
        self.ser = None
        self.cmd_queue = queue.Queue()

        # Start a dedicated worker thread for serial communication
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        # 1. Connect and allow ESP32 to reset
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Wait for ESP32 reset
            print("Connected to ESP32 Eyes")
        except Exception as e:
            print(f"EyeController Connection failed: {e}")
            return  # Exit if we can't connect

        # 2. Process commands sequentially
        while True:
            cmd = self.cmd_queue.get()
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write((cmd + '\n').encode())
                    self.ser.flush()  # Ensure data is sent to hardware before thread continues
                    print(f"Sent to Eyes: {cmd}")
                except Exception as e:
                    print(f"EyeController write error: {e}")

    def send(self, cmd):
        # Put command in queue instantly (does not block main loop)
        self.cmd_queue.put(cmd)

    # Emotion methods
    def happy(self):
        self.send('H')

    def sad(self):
        self.send('S')

    def cheer(self):
        self.send('C')

    def lovely(self):
        self.send('L')

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial to Eyes closed")
