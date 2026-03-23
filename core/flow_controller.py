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
        state_manager.current_path = []
        state_manager.set_affordance_level(1)

# Global singleton instance
flow_controller = FlowController()
