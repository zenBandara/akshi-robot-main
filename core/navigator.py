class Navigator:
    def __init__(self):
        self.stack = None
        self.screens = {}

    def register_screen(self, name, widget):
        if self.stack and widget not in [self.stack.widget(i) for i in range(self.stack.count())]:
            self.stack.addWidget(widget)
        self.screens[name] = widget

    def set_stack(self, stack):
        self.stack = stack
        for widget in self.screens.values():
            if widget not in [self.stack.widget(i) for i in range(self.stack.count())]:
                self.stack.addWidget(widget)

    def navigate_to(self, screen_name):
        if screen_name in self.screens and self.stack:
            widget = self.screens[screen_name]
            
            # Fire the on_hide lifecycle hook for the outgoing widget if it defines one
            current_widget = self.stack.currentWidget()
            if current_widget and hasattr(current_widget, "on_hide"):
                current_widget.on_hide()
                
            self.stack.setCurrentWidget(widget)
            
            # Telemetry Log
            from core.telemetry_logger import telemetry_logger
            telemetry_logger.log_event("SCREEN_TRANSITION", detail=f"Navigated to {screen_name}")
            
            # Fire the on_show lifecycle hook if the widget defines one
            if hasattr(widget, "on_show"):
                widget.on_show()
        else:
            print(f"Error: Cannot navigate to '{screen_name}'. Stack present: {self.stack is not None}")

# Global singleton
navigator = Navigator()
