from PySide6.QtCore import Qt

class KeyboardManager:
    def __init__(self):
        self.active_handler = None
        self.key_mapping = {
            Qt.Key_W: "WAKE",
            Qt.Key_S: "SKIP",
            Qt.Key_B: "BREAK",
            Qt.Key_C: "CONTINUE",
            Qt.Key_Return: "ENTER",
            Qt.Key_Enter: "ENTER",
        }
        
        # Add A-Z mappings
        for i in range(26):
            self.key_mapping[Qt.Key_A + i] = chr(ord('A') + i)
            
        # Add 0-9 mappings
        for i in range(10):
            self.key_mapping[Qt.Key_0 + i] = str(i)

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
