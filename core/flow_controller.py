from core.state_manager import state_manager
from core.transitions import switch_screen
from components.robot_eyes import get_robot_eyes

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CASCADE: Used ONLY during IDENTIFYING state (Question 1 for new students)
# Kinesthetic is a one-time side-loop between 1st and 2nd L1 attempt.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CASCADE = [
    "evaluate_L1",
    "engage",
    "evaluate_L2",
    "explore",
    "evaluate_L3",
    "explain",
    "evaluate_L3",
    "elaborate",
    "evaluate_L3",
    "teacher_intervention"
]

# Phase ladder: from most independent (index 0) to most scaffolded (index 4)
# "Above" means less scaffolding (lower index). "Below" means more scaffolding (higher index).
PHASE_LADDER = ["none", "engage", "explore", "explain", "elaborate"]

# Maps a phase to which scaffolding screen to show and what eval level to use
PHASE_SCREEN_MAP = {
    "none":      {"scaffolding": None,        "eval_level": 1},
    "engage":    {"scaffolding": "engage",     "eval_level": 2},
    "explore":   {"scaffolding": "explore",    "eval_level": 3},
    "explain":   {"scaffolding": "explain",    "eval_level": 3},
    "elaborate": {"scaffolding": "elaborate",  "eval_level": 3},
}

# Navigator screen IDs for cascade nodes
SCREEN_MAP = {
    "evaluate_L1": "evaluate",
    "evaluate_L2": "evaluate",
    "evaluate_L3": "evaluate",
    "elaborate": "elaborate",
    "explain": "explain",
    "explore": "explore",
    "engage": "engage",
    "teacher_intervention": "teacher_intervention"
}


class FlowController:
    def __init__(self):
        # ── CASCADE state (used during IDENTIFYING) ──
        self.cascade_index = 0
        self.kinesthetic_done = False
        
        # ── Progression state machine ──
        self.progression_state = "IDENTIFYING"  # "IDENTIFYING" | "CONFIRMING" | "ADVANCING"
        self.identified_phase = None            # e.g. "explore", "engage", "none"
        self.baseline_confirms = 0              # Need 2 to advance
        self.question_number = 0                # Which question we're on for this student

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILITY METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_current_node(self):
        """Returns the current structural stage (e.g., 'evaluate_L2')."""
        if self.cascade_index < len(CASCADE):
            return CASCADE[self.cascade_index]
        return "teacher_intervention"

    def reset_for_new_student(self):
        """Full reset for a brand new student."""
        self.cascade_index = 0
        self.kinesthetic_done = False
        self.progression_state = "IDENTIFYING"
        self.identified_phase = None
        self.baseline_confirms = 0
        self.question_number = 0
        state_manager.set_affordance_level(1)

    def reset_cascade(self):
        """Reset the cascade pointer (legacy compat + used during identification)."""
        self.cascade_index = 0
        self.kinesthetic_done = False
        state_manager.set_affordance_level(1)

    def _get_phase_above(self, phase):
        """Get the phase with less scaffolding (one step toward independence)."""
        idx = PHASE_LADDER.index(phase) if phase in PHASE_LADDER else -1
        if idx <= 0:
            return None  # Already at "none" (most independent)
        return PHASE_LADDER[idx - 1]

    def _get_eval_level_for_phase(self, phase):
        """Get the evaluation level for a given phase."""
        return PHASE_SCREEN_MAP.get(phase, {}).get("eval_level", 1)

    def _get_scaffolding_screen(self, phase):
        """Get the scaffolding screen name for a given phase."""
        return PHASE_SCREEN_MAP.get(phase, {}).get("scaffolding", None)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STUDENT FLOW ENTRY POINT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def start_student_flow(self, student_name):
        """
        Called when a new student is ready to start their questions.
        Checks DB history and decides: IDENTIFYING or CONFIRMING.
        """
        self.reset_for_new_student()

        # Check database for existing phase
        try:
            import core.database as database
            method_used, eval_passed = database.get_student_optimal_starting_method(student_name)
        except Exception as e:
            print(f"[FlowController] DB query failed, starting fresh: {e}")
            method_used, eval_passed = None, None

        print(f"[RL Intelligence] History for {student_name} -> Method: {method_used} | Passed: {eval_passed}")

        # Build the task queue for this student
        import core.task_loader as task_loader
        task_queue = task_loader.build_task_queue()
        state_manager.set_task_queue(task_queue)

        if method_used and method_used in PHASE_LADDER:
            # Returning student — skip identification, go straight to confirming
            self.identified_phase = method_used
            self.progression_state = "CONFIRMING"
            self.baseline_confirms = 0
            print(f"[FlowController] Returning student! Phase = '{method_used}'. Starting at CONFIRMING.")
            self._start_next_question()
        else:
            # New student — full cascade identification on Q1
            self.progression_state = "IDENTIFYING"
            self.question_number = 1
            print(f"[FlowController] New student! Starting IDENTIFYING cascade on Q1.")
            self._load_next_task_and_navigate_cascade()

    def _load_next_task_and_navigate_cascade(self):
        """Load the next task from queue and navigate to evaluate (cascade mode)."""
        task_queue = state_manager.get_task_queue()
        if task_queue:
            next_task = task_queue.pop(0)
            state_manager.set_task_queue(task_queue)
            state_manager.set_current_task(next_task)
            print(f"[FlowController] Loaded task: {next_task.get('task_id')} for cascade identification")
        
        # Reset cascade to beginning for this question
        self.cascade_index = 0
        self.kinesthetic_done = False
        state_manager.set_affordance_level(1)
        state_manager.current_path = []
        
        from core.navigator import navigator
        navigator.navigate_to("evaluate")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MULTI-QUESTION PROGRESSION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _start_next_question(self):
        """
        Load the next question and route to the appropriate scaffolding screen
        based on the current progression_state and identified_phase.
        """
        task_queue = state_manager.get_task_queue()
        
        if not task_queue:
            # No more questions — this student is done
            print(f"[FlowController] No more questions for this student. Moving to next student.")
            import core.session_logic as session_logic
            session_logic.next_student()
            return

        # Pop the next task
        next_task = task_queue.pop(0)
        state_manager.set_task_queue(task_queue)
        state_manager.set_current_task(next_task)
        self.question_number += 1
        state_manager.current_path = []

        print(f"[FlowController] ── Question {self.question_number} ── Task: {next_task.get('task_id')} | State: {self.progression_state} | Phase: {self.identified_phase}")

        if self.progression_state == "CONFIRMING":
            self._route_to_phase(self.identified_phase)
        elif self.progression_state == "ADVANCING":
            above_phase = self._get_phase_above(self.identified_phase)
            if above_phase:
                self._route_to_phase(above_phase)
            else:
                # Already at the top (none) — stay confirming
                print(f"[FlowController] Student is already at 'none' (most independent). Staying at baseline.")
                self.progression_state = "CONFIRMING"
                self._route_to_phase(self.identified_phase)

    def _route_to_phase(self, phase):
        """Navigate to the scaffolding screen for a phase, then evaluate."""
        from core.navigator import navigator

        scaffolding_screen = self._get_scaffolding_screen(phase)
        eval_level = self._get_eval_level_for_phase(phase)

        # Set the affordance level for the evaluation screen
        state_manager.set_affordance_level(eval_level)

        if scaffolding_screen:
            # Show scaffolding first, then evaluate (the scaffolding screen calls advance_cascade)
            print(f"[FlowController] Routing to scaffolding: {scaffolding_screen} → then evaluate L{eval_level}")
            state_manager.current_stage = phase
            navigator.navigate_to(scaffolding_screen)
        else:
            # Phase is "none" — go directly to evaluation
            print(f"[FlowController] Phase is 'none' — going directly to evaluate L{eval_level}")
            state_manager.current_stage = "evaluate_L1"
            navigator.navigate_to("evaluate")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CORRECT ANSWER HANDLING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def on_correct_answer(self, parent_widget):
        """Handle a correct answer — behavior depends on progression_state."""
        current_node = self.get_current_node()

        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
        if current_node not in state_manager.current_path:
            state_manager.current_path.append(current_node)

        print(f"[FlowController] ✅ Success at node: {current_node} | State: {self.progression_state}")
        get_robot_eyes().set_expression("surprised")

        if self.progression_state == "IDENTIFYING":
            self._handle_correct_identifying()
        elif self.progression_state == "CONFIRMING":
            self._handle_correct_confirming()
        elif self.progression_state == "ADVANCING":
            self._handle_correct_advancing()

    def _handle_correct_identifying(self):
        """Student passed during identification cascade. Store phase and transition."""
        # Determine which phase helped the student
        eval_map = {
            0: "none",       # Passed L1 independently
            2: "engage",     # Passed L2 after engage
            4: "explore",    # Passed L3 after explore
            6: "explain",    # Passed L3 after explain
            8: "elaborate",  # Passed L3 after elaborate
        }
        identified = eval_map.get(self.cascade_index, "none")
        self.identified_phase = identified

        # Log to database
        try:
            import core.database as database
            session_id = state_manager.get_current_session()
            student_name = state_manager.get_current_student() or "unknown"
            database.log_student_metric(session_id, student_name, f"evaluate_L{self._get_eval_level_for_phase(identified)}", identified)
        except Exception as db_err:
            print(f"[FlowController] DB logging error: {db_err}")

        print(f"[FlowController] 🎯 PHASE IDENTIFIED: '{identified}' for student {state_manager.get_current_student()}")

        # Transition to CONFIRMING for the next question
        self.progression_state = "CONFIRMING"
        self.baseline_confirms = 0

        # Navigate to celebration, which will trigger _start_next_question
        from core.navigator import navigator
        navigator.navigate_to("celebration")

    def _handle_correct_confirming(self):
        """Student passed at their baseline phase. Count confirmations."""
        self.baseline_confirms += 1
        print(f"[FlowController] Baseline confirmation {self.baseline_confirms}/2 for phase '{self.identified_phase}'")

        if self.baseline_confirms >= 2:
            # Ready to try the phase above!
            above = self._get_phase_above(self.identified_phase)
            if above:
                self.progression_state = "ADVANCING"
                print(f"[FlowController] 🚀 Baseline confirmed! Next question will try phase ABOVE: '{above}'")
            else:
                print(f"[FlowController] Student is already at 'none' (fully independent). Staying at baseline.")
                self.baseline_confirms = 0  # Keep cycling

        # Navigate to celebration, which will trigger _start_next_question
        from core.navigator import navigator
        navigator.navigate_to("celebration")

    def _handle_correct_advancing(self):
        """Student passed at a higher phase! PROMOTE!"""
        old_phase = self.identified_phase
        new_phase = self._get_phase_above(self.identified_phase)

        if new_phase:
            self.identified_phase = new_phase
            print(f"[FlowController] 🎉 PROMOTED! '{old_phase}' → '{new_phase}' is the new normal!")

            # Store the promotion in the database
            try:
                import core.database as database
                session_id = state_manager.get_current_session()
                student_name = state_manager.get_current_student() or "unknown"
                database.update_student_phase(session_id, student_name, new_phase)
            except Exception as db_err:
                print(f"[FlowController] DB promotion logging error: {db_err}")

        # Back to confirming at the NEW baseline
        self.progression_state = "CONFIRMING"
        self.baseline_confirms = 0

        from core.navigator import navigator
        navigator.navigate_to("celebration")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # INCORRECT ANSWER HANDLING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def on_incorrect_answer(self, parent_widget, is_timeout=False):
        """Handle an incorrect answer — behavior depends on progression_state."""
        current_node = self.get_current_node()
        log_node = f"{current_node}_timeout" if is_timeout else current_node

        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
        if log_node not in state_manager.current_path:
            state_manager.current_path.append(log_node)

        print(f"[FlowController] ❌ {'Timeout' if is_timeout else 'Incorrect'} at: {log_node} | State: {self.progression_state}")

        if is_timeout:
            get_robot_eyes().set_expression("thinking")
        else:
            get_robot_eyes().set_expression("encouraging")

        if self.progression_state == "IDENTIFYING":
            self._handle_incorrect_identifying(parent_widget, is_timeout)
        elif self.progression_state == "CONFIRMING":
            self._handle_incorrect_confirming()
        elif self.progression_state == "ADVANCING":
            self._handle_incorrect_advancing()

    def _handle_incorrect_identifying(self, parent_widget, is_timeout=False):
        """During identification, continue the cascade as before."""
        current_node = self.get_current_node()

        # ── KINESTHETIC SIDE-LOOP ──
        if current_node == "evaluate_L1" and not self.kinesthetic_done:
            self.kinesthetic_done = True
            print(f"[FlowController] First L1 failure → routing to Kinesthetic side-loop")
            state_manager.current_stage = "kinesthetic"
            try:
                from core.navigator import navigator
                navigator.navigate_to("kinestatic")
            except Exception as e:
                print(f"[FlowController] Routing error to kinesthetic: {e}")
            return

        # Normal cascade advancement
        self.cascade_index += 1
        next_node = self.get_current_node()
        print(f"[FlowController] Cascade escalation → {next_node}")

        if next_node == "evaluate_L2":
            state_manager.set_affordance_level(2)
        elif next_node == "evaluate_L3":
            state_manager.set_affordance_level(3)

        state_manager.current_stage = next_node

        try:
            from core.navigator import navigator
            nav_target = SCREEN_MAP.get(next_node)
            if nav_target:
                navigator.navigate_to(nav_target)
            else:
                print(f"[FlowController] Error: Unknown cascade node {next_node}")
        except Exception as e:
            print(f"[FlowController] Critical Routing Error: {e}")

    def _handle_incorrect_confirming(self):
        """Student failed at their baseline phase. Reset confirmations and try again."""
        self.baseline_confirms = 0
        print(f"[FlowController] Failed at baseline '{self.identified_phase}'. Resetting confirms. Next question = same phase.")

        # Load next question at the same phase
        self._start_next_question()

    def _handle_incorrect_advancing(self):
        """Student failed at the higher phase. Fall back to identified phase."""
        print(f"[FlowController] Failed advancement! Falling back to baseline '{self.identified_phase}'. Resetting confirms.")
        self.progression_state = "CONFIRMING"
        self.baseline_confirms = 0

        # Load next question at the original baseline phase
        self._start_next_question()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SCAFFOLDING SCREEN COMPLETIONS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def advance_cascade(self, parent_widget=None):
        """Called when a scaffolding screen (engage/explore/explain/elaborate) finishes.
        Routes to the appropriate evaluation screen."""

        if self.progression_state == "IDENTIFYING":
            # During identification, advance the cascade index normally
            self.cascade_index += 1
            next_node = self.get_current_node()
            print(f"[FlowController] Cascade advancing to: {next_node}")

            if next_node == "evaluate_L2":
                state_manager.set_affordance_level(2)
            elif next_node == "evaluate_L3":
                state_manager.set_affordance_level(3)

            state_manager.current_stage = next_node

            try:
                from core.navigator import navigator
                nav_target = SCREEN_MAP.get(next_node)
                if nav_target:
                    navigator.navigate_to(nav_target)
            except Exception:
                pass
        else:
            # During CONFIRMING/ADVANCING, scaffolding is done → go to evaluate
            if self.progression_state == "ADVANCING":
                phase = self._get_phase_above(self.identified_phase)
            else:
                phase = self.identified_phase
            
            eval_level = self._get_eval_level_for_phase(phase) if phase else 1
            state_manager.set_affordance_level(eval_level)
            state_manager.current_stage = f"evaluate_L{eval_level}"

            print(f"[FlowController] Scaffolding done → evaluate L{eval_level}")
            try:
                from core.navigator import navigator
                navigator.navigate_to("evaluate")
            except Exception:
                pass

    def advance_after_kinesthetic(self, parent_widget):
        """Called when the kinesthetic activity is done. Returns to evaluate_L1 for a retry."""
        print("[FlowController] Kinesthetic activity complete. Returning to evaluate_L1 for retry...")
        state_manager.current_stage = "evaluate_L1"
        try:
            from core.navigator import navigator
            navigator.navigate_to("evaluate")
        except Exception as e:
            print(f"[FlowController] CRITICAL: Could not return to Evaluation Screen. {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TIMEOUT / SKIP / BREAK
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def on_timeout(self, parent_widget):
        """Treat an evaluation inactivity timeout identically to an incorrect answer."""
        self.on_incorrect_answer(parent_widget, is_timeout=True)

    def on_skip(self, parent_widget):
        """Handle an explicit student skip request natively."""
        current_node = self.get_current_node()

        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
        if current_node not in state_manager.current_path:
            state_manager.current_path.append(current_node)

        print(f"[FlowController] Explicit Skip triggered at: {current_node}")

        # Log Result (Skipped)
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
        except ImportError:
            pass

        print(f"[FlowController] LOGGED SKIP EVENT: {log_data}")

        # Move to next student
        import core.session_logic as session_logic
        session_logic.next_student()

    def on_break(self, parent_widget):
        """Safely pause the execution cascade natively without destroying state indexes."""
        print(f"[FlowController] Child requested break! Pausing at node: {self.get_current_node()}")
        get_robot_eyes().set_expression("sleeping")

        try:
            from core.navigator import navigator
            navigator.navigate_to("break")
        except Exception:
            pass

    def resume_cascade(self, parent_widget):
        """Restore exact execution state after a break."""
        current_node = self.get_current_node()
        get_robot_eyes().set_expression("default")
        print(f"[FlowController] Break resolved. Resuming at node: {current_node}")

        try:
            from core.navigator import navigator
            nav_target = SCREEN_MAP.get(current_node)
            if nav_target:
                navigator.navigate_to(nav_target)
        except Exception as e:
            print(f"[FlowController] Error resuming cascade at {current_node}: {e}")


# Global singleton instance
flow_controller = FlowController()
