from core.state_manager import state_manager

# Define the absolute deterministic sequence for a failing student
CASCADE = [
    "evaluate_L1", 
    "elaborate", 
    "evaluate_L2", 
    "explain", 
    "evaluate_L3", 
    "explore", 
    "evaluate_L3", 
    "engage", 
    "evaluate_L3", 
    "teacher_intervention"
]

class FlowController:
    def __init__(self):
        # The physical string-index pointer into the CASCADE sequence
        self.cascade_index = 0
        
    def get_current_node(self):
        """Returns the current structural stage (e.g., 'evaluate_L2')."""
        if self.cascade_index < len(CASCADE):
            return CASCADE[self.cascade_index]
        return "teacher_intervention"

    def reset_cascade(self):
        """Reset the cascade pointer unconditionally (e.g. for a new task or student)."""
        self.cascade_index = 0
        state_manager.set_affordance_level(1)
        # We do NOT wipe state_manager.current_path here because celebration_screen needs it to log Firebase telemetry first!

    def on_correct_answer(self, parent_widget):
        """Handle a correct answer resolution."""
        current_node = self.get_current_node()
        
        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
            
        if current_node not in state_manager.current_path:
            state_manager.current_path.append(current_node)
            
        print(f"[FlowController] Success triggered at node: {current_node}")
        
        # Reset cascade pointer safely for the next student
        self.reset_cascade()
        
        # Trigger the Celebration path (which implicitly calls next_student() after the animations)
        try:
            from screens import celebration_screen
            if parent_widget:
                celeb_ui = celebration_screen.get_ui()
                parent_widget.addWidget(celeb_ui)
                parent_widget.setCurrentWidget(celeb_ui)
        except ImportError:
            print("[FlowController] CRITICAL: Could not transit to Celebration Screen.")

# Global singleton instance
flow_controller = FlowController()
