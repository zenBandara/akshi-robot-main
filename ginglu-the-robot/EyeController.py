import serial
import time
import threading

class EyeController:
    def __init__(self):
        self.port = '/dev/ttyACM0'
        self.baudrate = 115200
        self.timeout = 1
        self.ser = None

        # Connect in a background thread so the 2-second sleep doesn't block startup
        threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # wait for ESP32 reset
            print("Connected to ESP32")
        except Exception as e:
            print(f"Connection failed: {e}")

    def send(self, cmd):
        def _send_task():
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write((cmd + '\n').encode())
                    print(f"Sent: {cmd}")
                except Exception as e:
                    print(f"Serial write error: {e}")
            else:
                print("Serial not connected")
                
        # Send in a background thread so serial lag doesn't block the camera loop
        threading.Thread(target=_send_task, daemon=True).start()

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
            print("Serial closed")