import threading
from PySide6.QtCore import Qt, QObject, Signal

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Toggle this to switch between keyboard and AI Thinker voice input
# False = Keyboard only (development laptop)
# True  = AI Thinker VC-02 voice input + keyboard fallback (Raspberry Pi)
USE_VOICE_INPUT = False
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Test


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
            Qt.Key_T: "BREAK",  # T for Tired/Take a break (B reassigned to BYE)
            Qt.Key_B: "BYE",
            Qt.Key_Return: "ENTER",
            Qt.Key_Enter: "ENTER",
            Qt.Key_Escape: "ESCAPE",
            Qt.Key_Z: "STOP",
            Qt.Key_Q: "STOP",
        }
        
        # Add A-Z mappings ONLY if they aren't already mapped
        for i in range(26):
            key_code = Qt.Key_A + i
            if key_code not in self.key_mapping:
                self.key_mapping[key_code] = chr(ord('A') + i)
            
        # Add 0-9 mappings
        for i in range(10):
            self.key_mapping[Qt.Key_0 + i] = str(i)

        # ── Override: 1 = YES, 2 = NO (for voice-driven evaluation) ──
        self.key_mapping[Qt.Key_1] = "YES"
        self.key_mapping[Qt.Key_2] = "NO"

        # ── Voice Command Hex Mappings (VC-02 → Action) ──
        # Based on lecturer's pre-programmed AI Thinker firmware
        self.voice_hex_mapping = {
            0x01: "WAKE",       # "Start Command 'Ging-lu'"
            0x02: "YES",        # "Said Yes"
            0x03: "NO",         # "Said No"
            0x10: "SKIP",       # "Skip" command
            0x08: "BREAK",      # "I'm tired" (Reusing for Take a break)
            0x09: "ENTER",      # "Said Ok" (Used for pass/continue)
            0x11: "STOP",       # "Stop" command
            0x12: "BYE",        # "Said Bye"
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
        if action == "STOP":
            self.global_emergency_stop()
            return
            
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
            
        if mapped_action == "STOP":
            self.global_emergency_stop()
            return
            
        if self.active_handler and mapped_action:
            self.active_handler(mapped_action)

    def global_emergency_stop(self):
        print("🚨 [GLOBAL STOP] Emergency HARD RESET Triggered! Restarting entire application...")
        from core.voice_manager import VoiceManager
        try:
            VoiceManager().stop()
        except Exception:
            pass

        # 1. Stop the backend subprocess so it doesn't leak or hold the camera hostage
        try:
            import core.backend_manager as backend_manager
            backend_manager.stop()
        except Exception as e:
            print(f"[GLOBAL STOP] Warning: Could not stop backend manager: {e}")

        # 2. Reset the IPC JSON file
        from core.ipc_queue import append_ipc_command
        try:
            append_ipc_command({"type": "end_session"}, "ginglu-the-robot/calibration_command.json")
        except Exception:
            pass

        # 3. Hard Restart! Kill the current process and spawn a perfectly fresh one.
        import os
        import sys
        print("♻️ [GLOBAL STOP] Executing process reboot...")
        os.execl(sys.executable, sys.executable, *sys.argv)

# Global singleton instance
keyboard_manager = KeyboardManager()
