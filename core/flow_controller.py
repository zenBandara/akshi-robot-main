from core.state_manager import state_manager
from core.transitions import switch_screen
from components.robot_eyes import get_robot_eyes

# Define the absolute deterministic sequence for a failing student
CASCADE = [
    "evaluate_L1", 
    "kinesthetic", 
    "engage", 
    "evaluate_L2", 
    "explore", 
    "evaluate_L3", 
    "explain", 
    "evaluate_L3", 
    "elaborate",
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
        get_robot_eyes().set_expression("surprised")
        
        # Reset cascade pointer safely for the next student
        self.reset_cascade()
        
        # Trigger the Celebration path (which implicitly calls next_student() after the animations)
        try:
            from core.navigator import navigator
            navigator.navigate_to("celebration")
        except Exception as e:
            print(f"[FlowController] CRITICAL: Could not transit to Celebration Screen. {e}")

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
        
        if is_timeout:
            get_robot_eyes().set_expression("thinking")
        else:
            get_robot_eyes().set_expression("encouraging")
        
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
            from core.navigator import navigator
            
            # Map logical cascade nodes to navigator string IDs
            screen_map = {
                "evaluate_L1": "evaluate",
                "evaluate_L2": "evaluate",
                "evaluate_L3": "evaluate",
                "kinesthetic": "kinestatic",
                "elaborate": "elaborate",
                "explain": "explain",
                "explore": "explore",
                "engage": "engage",
                "teacher_intervention": "teacher_intervention"
            }
            
            nav_target = screen_map.get(next_node)
            if nav_target:
                navigator.navigate_to(nav_target)
            else:
                print(f"[FlowController] Error: Unknown cascade node {next_node}")
        except Exception as e:
            print(f"[FlowController] Critical Routing Error escalating out to {next_node}: {e}")

    def advance_cascade(self, parent_widget=None):
        """Cleanly advance the cascade sequence without marking it as a 'failure', e.g. for non-evaluation nodes like Engage."""
        self.cascade_index += 1
        next_node = self.get_current_node()
        print(f"[FlowController] Continuing cascade sequence natively to: {next_node}")
        
        if next_node == "evaluate_L2":
            state_manager.set_affordance_level(2)
        elif next_node == "evaluate_L3":
            state_manager.set_affordance_level(3)
            
        state_manager.current_stage = next_node
        
        try:
            from core.navigator import navigator
            screen_map = {
                "evaluate_L1": "evaluate",
                "evaluate_L2": "evaluate",
                "evaluate_L3": "evaluate",
                "kinesthetic": "kinestatic",
                "elaborate": "elaborate",
                "explain": "explain",
                "explore": "explore",
                "engage": "engage",
                "teacher_intervention": "teacher_intervention"
            }
            nav_target = screen_map.get(next_node)
            if nav_target:
                navigator.navigate_to(nav_target)
        except Exception: pass

    def on_timeout(self, parent_widget):
        """Treat an evaluation inactivity timeout identically to an incorrect answer cascade."""
        self.on_incorrect_answer(parent_widget, is_timeout=True)

    def on_kinesthetic_fail(self, parent_widget):
        # Escalate directly mimicking an evaluation failure
        self.on_incorrect_answer(parent_widget)

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
                from core.navigator import navigator
                navigator.navigate_to("greeting")
            except Exception: pass
        else:
            try:
                from core.navigator import navigator
                navigator.navigate_to("session_complete")
            except Exception: pass

    def on_break(self, parent_widget):
        """Safely pause the execution cascade natively without destroying state indexes."""
        print(f"[FlowController] Child requested break! Pausing cascade at node: {self.get_current_node()}")
        get_robot_eyes().set_expression("sleeping")
        
        try:
            from core.navigator import navigator
            navigator.navigate_to("break")
        except Exception: pass

    def resume_cascade(self, parent_widget):
        """Restore exact execution state to the specific cascade pointer node logically mapped prior to Break condition."""
        current_node = self.get_current_node()
        get_robot_eyes().set_expression("default")
        print(f"[FlowController] Break resolved. Resuming cascade execution identically at node: {current_node}")
        
        try:
            from core.navigator import navigator
            screen_map = {
                "evaluate_L1": "evaluate",
                "evaluate_L2": "evaluate",
                "evaluate_L3": "evaluate",
                "kinesthetic": "kinestatic",
                "elaborate": "elaborate",
                "explain": "explain",
                "explore": "explore",
                "engage": "engage",
                "teacher_intervention": "teacher_intervention"
            }
            nav_target = screen_map.get(current_node)
            if nav_target:
                navigator.navigate_to(nav_target)
        except Exception as e:
            print(f"[FlowController] Error attempting to resume cascade at {current_node}: {e}")

# Global singleton instance
flow_controller = FlowController()
