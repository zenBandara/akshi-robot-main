import threading
from PySide6.QtCore import Qt, QObject, Signal

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Toggle this to switch between keyboard and AI Thinker voice input
# False = Keyboard only (development laptop)
# True  = AI Thinker VC-02 voice input + keyboard fallback (Raspberry Pi)
USE_VOICE_INPUT = False
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class VoiceSignalBridge(QObject):
    """Thread-safe bridge: emits a Qt Signal from the serial thread
    so the main UI thread can safely process voice commands."""
    voice_command_received = Signal(str)


class KeyboardManager:
    def __init__(self):
        self.active_handler = None

        # ── Keyboard Mappings (unchanged) ──
        self.key_mapping = {
            Qt.Key_W: "WAKE",
            Qt.Key_S: "SKIP",
            Qt.Key_B: "BREAK",
            Qt.Key_C: "CONTINUE",
            Qt.Key_Return: "ENTER",
            Qt.Key_Enter: "ENTER",
        }
        
        # Add A-Z mappings ONLY if they aren't already mapped
        for i in range(26):
            key_code = Qt.Key_A + i
            if key_code not in self.key_mapping:
                self.key_mapping[key_code] = chr(ord('A') + i)
            
        # Add 0-9 mappings
        for i in range(10):
            self.key_mapping[Qt.Key_0 + i] = str(i)

        # ── Voice Command Hex Mappings (VC-02 → Action) ──
        self.voice_hex_mapping = {
            0x01: "WAKE",       # "Hey Akshi" / "Wake up"
            0x02: "1",          # "Option one"
            0x03: "2",          # "Option two"
            0x04: "3",          # "Option three"
            0x05: "4",          # "Option four"
            0x06: "ENTER",      # "Next" / "Continue"
            0x07: "CONTINUE",   # "Teacher continue"
            0x08: "SKIP",       # "Skip"
            0x09: "BREAK",      # "Take a break"
            0x0A: "P",          # "Pass"
            0x0B: "F",          # "Fail"
            0x0C: "CONTINUE",   # "Select teacher"
        }

        # ── Voice Input Thread (Raspberry Pi only) ──
        self.voice_bridge = VoiceSignalBridge()
        self.voice_bridge.voice_command_received.connect(self._on_voice_command)

        if USE_VOICE_INPUT:
            self._start_serial_listener()
        else:
            print("[Input Manager] Voice input DISABLED. Keyboard-only mode.")

    def _start_serial_listener(self):
        """Start background thread to read VC-02 serial data."""
        def listen():
            import serial
            import time
            try:
                ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
                print("[Voice Input] ✅ Serial port opened. Listening for VC-02...")
            except Exception as e:
                print(f"[Voice Input] ❌ FAILED to open serial port: {e}")
                print("[Voice Input] Falling back to keyboard-only mode.")
                return

            while True:
                try:
                    if ser.in_waiting >= 2:
                        start_byte = ser.read(1)[0]
                        cmd_byte = ser.read(1)[0]

                        if start_byte == 0xAA:
                            action = self.voice_hex_mapping.get(cmd_byte)
                            if action:
                                print(f"[Voice Input] 🎤 AA {cmd_byte:02X} → {action}")
                                self.voice_bridge.voice_command_received.emit(action)
                            else:
                                print(f"[Voice Input] ⚠️ Unknown command: AA {cmd_byte:02X}")
                    else:
                        time.sleep(0.03)
                except Exception as e:
                    print(f"[Voice Input] Read error: {e}")
                    time.sleep(1)

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
        print("[Voice Input] 🎤 AI Thinker serial listener thread started.")

    def _on_voice_command(self, action: str):
        """Called on the MAIN UI thread when a voice command arrives via Signal."""
        if self.active_handler:
            self.active_handler(action)

    def register_handler(self, handler_function):
        """Register the current active screen's key handler."""
        self.active_handler = handler_function

    def unregister_handler(self):
        """Unregister the active screen's handler."""
        self.active_handler = None

    def handle_key_press(self, event):
        """Process key press and pass string action to active handler if registered."""
        key = event.key()
        mapped_action = self.key_mapping.get(key)
        
        # Fallback to key text if not in our predefined mappings (e.g. lowercase letters if needed)
        # But Qt.Key always returns uppercase constants for letter keys
        if not mapped_action and event.text().upper():
            mapped_action = event.text().upper()
            
        if self.active_handler and mapped_action:
            self.active_handler(mapped_action)

# Global singleton instance
keyboard_manager = KeyboardManager()
