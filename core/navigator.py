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
            self.stack.setCurrentWidget(self.screens[screen_name])
        else:
            print(f"Error: Cannot navigate to '{screen_name}'. Stack present: {self.stack is not None}")

# Global singleton
navigator = Navigator()
