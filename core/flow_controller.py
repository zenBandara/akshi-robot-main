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

    def on_incorrect_answer(self, parent_widget, is_timeout=False):
        """Handle an incorrect answer by deeply escalating the cognitive cascade."""
        current_node = self.get_current_node()
        log_node = f"{current_node}_timeout" if is_timeout else current_node
        
        # 1. Store the exact point of numerical failure into the path array
        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
        if log_node not in state_manager.current_path:
            state_manager.current_path.append(log_node)
            
        print(f"[FlowController] {'Timeout' if is_timeout else 'Incorrect Answer'} caught at: {log_node}")
        
        # 2. Advance the pointer strictly by 1 scalar index unit
        self.cascade_index += 1
        next_node = self.get_current_node()
        print(f"[FlowController] Escalating simulation natively to next cascade node: {next_node}")
        
        # 3. Modify global logical evaluation structural scaling natively
        if next_node == "evaluate_L2":
            state_manager.set_affordance_level(2)
        elif next_node == "evaluate_L3":
            state_manager.set_affordance_level(3)
            
        # Update logical 5e_stage directly into the unified tracker implicitly
        state_manager.current_stage = next_node
            
        # 4. Synthesize visual routing
        try:
            target_ui = None
            if next_node == "elaborate":
                from screens import elaborate_screen
                target_ui = elaborate_screen.get_ui()
            elif next_node in ["evaluate_L1", "evaluate_L2", "evaluate_L3"]:
                from screens import evaluate_screen
                target_ui = evaluate_screen.get_ui()
            elif next_node == "explain":
                from screens import explain_screen
                target_ui = explain_screen.get_ui()
            elif next_node == "explore":
                from screens import explore_screen
                target_ui = explore_screen.get_ui()
            elif next_node == "engage":
                from screens import engage_screen
                target_ui = engage_screen.get_ui()
            elif next_node == "teacher_intervention":
                from screens import teacher_intervention
                target_ui = teacher_intervention.get_ui()
                
            if parent_widget and target_ui:
                parent_widget.addWidget(target_ui)
                parent_widget.setCurrentWidget(target_ui)
            else:
                print(f"[FlowController] Error: Failed to load target GUI framework for cascade node {next_node}")
        except ImportError as e:
            print(f"[FlowController] Critical Routing Error escalating out to {next_node}: {e}")

    def on_timeout(self, parent_widget):
        """Treat an evaluation inactivity timeout identically to an incorrect answer cascade."""
        self.on_incorrect_answer(parent_widget, is_timeout=True)

    def on_skip(self, parent_widget):
        """Handle an explicit student skip request natively."""
        current_node = self.get_current_node()
        
        # 1. Store the exact point of the skip
        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
        if current_node not in state_manager.current_path:
            state_manager.current_path.append(current_node)
            
        print(f"[FlowController] Explicit Skip triggered natively at cascade node: {current_node}")
        
        # 2. Log Result (Skipped)
        task_data = state_manager.get_current_task()
        task_id = task_data.get("task_id", "unknown") if task_data else "unknown"
        student_id = state_manager.get_current_student() or "unknown"
        
        log_data = {
            "student_id": student_id,
            "task_id": task_id,
            "result": "skipped",
            "affordance_level_reached": getattr(state_manager, "affordance_level", 1),
            "path_taken": state_manager.current_path
        }
        
        if not hasattr(state_manager, 'session_logs'):
            state_manager.session_logs = []
        state_manager.session_logs.append(log_data)
        
        try:
            from core import firebase
            firebase.log_event(log_data)
        except ImportError: pass
            
        print(f"[FlowController] LOGGED SKIP EVENT: {log_data}")
        
        # 3. Advance Queue Natively
        student_queue = state_manager.get_student_queue()
        
        if student_queue:
            next_stu = student_queue.pop(0)
            state_manager.set_current_student(next_stu)
            state_manager.set_student_queue(student_queue)
            
            # 4. Wipe affordance tracking state completely for the next child
            self.reset_cascade()
            state_manager.current_path = []
            
            try:
                from screens import greeting_screen
                if parent_widget:
                    greeting_ui = greeting_screen.get_ui()
                    parent_widget.addWidget(greeting_ui)
                    parent_widget.setCurrentWidget(greeting_ui)
            except ImportError: pass
        else:
            try:
                from screens import session_complete
                if parent_widget:
                    session_complete_ui = session_complete.get_ui()
                    parent_widget.addWidget(session_complete_ui)
                    parent_widget.setCurrentWidget(session_complete_ui)
            except ImportError: pass

    def on_break(self, parent_widget):
        """Safely pause the execution cascade natively without destroying state indexes."""
        print(f"[FlowController] Child requested break! Pausing cascade at node: {self.get_current_node()}")
        
        try:
            from screens import break_screen
            if parent_widget:
                break_ui = break_screen.get_ui()
                parent_widget.addWidget(break_ui)
                parent_widget.setCurrentWidget(break_ui)
        except ImportError: pass

    def resume_cascade(self, parent_widget):
        """Restore exact execution state to the specific cascade pointer node logically mapped prior to Break condition."""
        current_node = self.get_current_node()
        print(f"[FlowController] Break resolved. Resuming cascade execution identically at node: {current_node}")
        
        try:
            target_ui = None
            if current_node == "elaborate":
                from screens import elaborate_screen
                target_ui = elaborate_screen.get_ui()
            elif current_node in ["evaluate_L1", "evaluate_L2", "evaluate_L3"]:
                from screens import evaluate_screen
                target_ui = evaluate_screen.get_ui()
            elif current_node == "explain":
                from screens import explain_screen
                target_ui = explain_screen.get_ui()
            elif current_node == "explore":
                from screens import explore_screen
                target_ui = explore_screen.get_ui()
            elif current_node == "engage":
                from screens import engage_screen
                target_ui = engage_screen.get_ui()
            elif current_node == "teacher_intervention":
                from screens import teacher_intervention
                target_ui = teacher_intervention.get_ui()
                
            if parent_widget and target_ui:
                parent_widget.addWidget(target_ui)
                parent_widget.setCurrentWidget(target_ui)
        except ImportError as e:
            print(f"[FlowController] Error attempting to resume cascade at {current_node}: {e}")

# Global singleton instance
flow_controller = FlowController()
