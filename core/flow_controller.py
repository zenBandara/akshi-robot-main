from core.state_manager import state_manager
from core.transitions import switch_screen
from components.robot_eyes import get_robot_eyes

# CASCADE: Used ONLY during IDENTIFYING state (Q1 for new students)
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

PHASE_LADDER = ["none", "engage", "explore", "explain", "elaborate"]

PHASE_SCREEN_MAP = {
    "none":      {"scaffolding": None,        "eval_level": 1},
    "engage":    {"scaffolding": "engage",     "eval_level": 2},
    "explore":   {"scaffolding": "explore",    "eval_level": 3},
    "explain":   {"scaffolding": "explain",    "eval_level": 3},
    "elaborate": {"scaffolding": "elaborate",  "eval_level": 3},
}

SCREEN_MAP = {
    "evaluate_L1": "evaluate", "evaluate_L2": "evaluate", "evaluate_L3": "evaluate",
    "elaborate": "elaborate", "explain": "explain", "explore": "explore",
    "engage": "engage", "teacher_intervention": "teacher_intervention"
}


class FlowController:
    def __init__(self):
        self.cascade_index = 0
        self.kinesthetic_used_at = set()
        self.progression_state = "IDENTIFYING"
        self.identified_phase = None
        self.baseline_confirms = 0
        self.used_kinesthetic_this_round = False

    # ── State Persistence ──

    def _save_student_state(self, student_name):
        try:
            import core.database as database
            database.save_student_state(student_name, self.progression_state, self.identified_phase, self.baseline_confirms)
        except Exception as e:
            print(f"[FlowController] DB Save error: {e}")

    def _load_student_state(self, student_name):
        try:
            import core.database as database
            row = database.load_student_state(student_name)
            if row:
                self.progression_state, self.identified_phase, self.baseline_confirms = row
                return True
        except Exception as e:
            print(f"[FlowController] DB Load error: {e}")
        return False

    # ── Utilities ──

    def get_current_node(self):
        if self.cascade_index < len(CASCADE):
            return CASCADE[self.cascade_index]
        return "teacher_intervention"

    def reset_for_new_student(self):
        self.cascade_index = 0
        self.kinesthetic_used_at = set()
        self.used_kinesthetic_this_round = False
        state_manager.set_affordance_level(1)
        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
        state_manager.current_path = []

    def reset_cascade(self):
        self.cascade_index = 0
        self.kinesthetic_used_at = set()
        self.used_kinesthetic_this_round = False
        state_manager.set_affordance_level(1)

    def _get_phase_above(self, phase):
        idx = PHASE_LADDER.index(phase) if phase in PHASE_LADDER else -1
        if idx <= 0:
            return None
        return PHASE_LADDER[idx - 1]

    def _get_eval_level(self, phase):
        return PHASE_SCREEN_MAP.get(phase, {}).get("eval_level", 1)

    def _get_scaffolding(self, phase):
        return PHASE_SCREEN_MAP.get(phase, {}).get("scaffolding", None)

    # ── Entry Point ──

    def start_student_flow(self, student_name):
        """Called when a student is ready. ONE question per student per round."""
        self.reset_for_new_student()

        # Try to restore permanently saved state from database
        if self._load_student_state(student_name):
            print(f"[FlowController] Restored {student_name} from DB: {self.progression_state} | Phase: {self.identified_phase} | Confirms: {self.baseline_confirms}")
            self._route_for_progression()
            return
            
        # If absolutely no record exists in student_states or metrics, brand new student!
        self.progression_state = "IDENTIFYING"
        self.identified_phase = "none"
        self.baseline_confirms = 0
        print(f"[FlowController] Brand new student {student_name} → IDENTIFYING cascade")
        from core.navigator import navigator
        navigator.navigate_to("evaluate")

    def _route_for_progression(self):
        """Route to the correct screen for CONFIRMING or ADVANCING states."""
        if self.progression_state == "ADVANCING":
            phase = self._get_phase_above(self.identified_phase)
            if not phase:
                self.progression_state = "CONFIRMING"
                phase = self.identified_phase
        else:
            phase = self.identified_phase
        self._route_to_phase(phase)

    def _route_to_phase(self, phase):
        from core.navigator import navigator
        scaffolding = self._get_scaffolding(phase)
        eval_level = self._get_eval_level(phase)
        state_manager.set_affordance_level(eval_level)

        phase_to_eval_index = {"none": 0, "engage": 2, "explore": 4, "explain": 6, "elaborate": 8}

        if scaffolding:
            self.cascade_index = max(0, phase_to_eval_index.get(phase, 0) - 1)
            print(f"[FlowController] Routing → {scaffolding} → then evaluate L{eval_level}")
            state_manager.current_stage = phase
            navigator.navigate_to(scaffolding)
        else:
            self.cascade_index = phase_to_eval_index.get(phase, 0)
            print(f"[FlowController] Phase 'none' → directly to evaluate L{eval_level}")
            state_manager.current_stage = "evaluate_L1"
            navigator.navigate_to("evaluate")

    # ── Correct Answer ──

    def on_correct_answer(self, parent_widget):
        current_node = self.get_current_node()
        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
        if current_node not in state_manager.current_path:
            state_manager.current_path.append(current_node)

        print(f"[FlowController] ✅ Success at: {current_node} | State: {self.progression_state}")
        
        # Telemetry Log
        from core.telemetry_logger import telemetry_logger
        telemetry_logger.log_event("EVALUATION_RESULT", detail=f"Correct at {current_node}", is_correct=True)

        get_robot_eyes().set_expression("surprised")

        student_name = state_manager.get_current_student() or "unknown"

        if self.progression_state == "IDENTIFYING":
            # Determine which phase helped
            eval_map = {0: "none", 2: "engage", 4: "explore", 6: "explain", 8: "elaborate"}
            self.identified_phase = eval_map.get(self.cascade_index, "none")
            self.progression_state = "CONFIRMING"
            self.baseline_confirms = 0
            print(f"[FlowController] 🎯 IDENTIFIED: '{self.identified_phase}'")
            
            # Telemetry Log
            from core.telemetry_logger import telemetry_logger
            telemetry_logger.log_event("IDENTIFIED", detail=f"Identified baseline phase: {self.identified_phase}")

            try:
                import core.database as database
                session_id = state_manager.get_current_session()
                # Check if we just came from teacher intervention (though identifying usually doesn't)
                ti = 1 if self.get_current_node() == "teacher_intervention" else 0
                database.log_student_metric(session_id, student_name,
                    f"evaluate_L{self._get_eval_level(self.identified_phase)}", 
                    self.identified_phase,
                    used_kinesthetic=self.used_kinesthetic_this_round,
                    teacher_intervention=ti)
            except Exception as e:
                print(f"[FlowController] DB error: {e}")

        elif self.progression_state == "CONFIRMING":
            self.baseline_confirms += 1
            print(f"[FlowController] Baseline confirm {self.baseline_confirms}/2 for '{self.identified_phase}'")
            if self.baseline_confirms >= 2:
                above = self._get_phase_above(self.identified_phase)
                if above:
                    self.progression_state = "ADVANCING"
                    print(f"[FlowController] 🚀 Ready to advance! Next round tries '{above}'")
                else:
                    self.baseline_confirms = 0  # Already at top

        elif self.progression_state == "ADVANCING":
            old = self.identified_phase
            new = self._get_phase_above(self.identified_phase)
            if new:
                self.identified_phase = new
                print(f"[FlowController] 🎉 PROMOTED: '{old}' → '{new}'")
                
                # Telemetry Log
                from core.telemetry_logger import telemetry_logger
                telemetry_logger.log_event("PROMOTION", detail=f"Promoted from {old} to {new}")

                try:
                    import core.database as database
                    session_id = state_manager.get_current_session()
                    database.update_student_phase(session_id, student_name, new, 
                                                 used_kinesthetic=self.used_kinesthetic_this_round,
                                                 teacher_intervention=0) # Advancement implies they passed without TI
                except Exception as e:
                    print(f"[FlowController] DB error: {e}")
            self.progression_state = "CONFIRMING"
            self.baseline_confirms = 0

        self._save_student_state(student_name)
        self.reset_cascade()

        from core.navigator import navigator
        navigator.navigate_to("celebration")

    # ── Incorrect Answer ──

    def on_incorrect_answer(self, parent_widget, is_timeout=False):
        current_node = self.get_current_node()
        # If we are in CONFIRMING/ADVANCING, get_current_node() might not be accurate 
        # for what's actually on screen. Let's determine the level.
        level = state_manager.get_affordance_level()
        log_node = f"{current_node}_timeout" if is_timeout else current_node
        
        if not hasattr(state_manager, 'current_path'):
            state_manager.current_path = []
        if log_node not in state_manager.current_path:
            state_manager.current_path.append(log_node)

        print(f"[FlowController] ❌ {'Timeout' if is_timeout else 'Incorrect'} at level {level} | State: {self.progression_state}")
        
        # Telemetry Log
        from core.telemetry_logger import telemetry_logger
        telemetry_logger.log_event(
            "TIMEOUT" if is_timeout else "EVALUATION_RESULT", 
            detail=f"{'Timeout' if is_timeout else 'Incorrect'} at L{level} ({current_node})",
            is_correct=False
        )

        if is_timeout:
            get_robot_eyes().set_expression("thinking")
        else:
            get_robot_eyes().set_expression("encouraging")

        # ── KINESTHETIC LOOP (Per cascade node — each evaluate node gets its own kinesthetic chance) ──
        if self.cascade_index not in self.kinesthetic_used_at:
            self.kinesthetic_used_at.add(self.cascade_index)
            self.used_kinesthetic_this_round = True
            print(f"[FlowController] First L{level} failure at cascade[{self.cascade_index}] → Kinesthetic side-loop")
            state_manager.current_stage = "kinesthetic"
            try:
                from core.navigator import navigator
                navigator.navigate_to("kinestatic")
                return
            except Exception as e:
                print(f"[FlowController] Routing error: {e}")

        # If kinesthetic was already tried, proceed with state-specific logic
        if self.progression_state != "IDENTIFYING":
            print(f"[FlowController] Failed baseline/advancement. Dropping to IDENTIFYING cascade.")
            
            # Telemetry Log
            from core.telemetry_logger import telemetry_logger
            telemetry_logger.log_event("DOWNGRADE", detail=f"Failed {self.progression_state} at {current_node}. Dropping to IDENTIFYING.")

            self.baseline_confirms = 0
            self.progression_state = "IDENTIFYING"

        self._cascade_incorrect(parent_widget, is_timeout=is_timeout)
                return
            elif self.progression_state == "CONFIRMING":
                # Failed baseline — drop to cascade to re-identify
                print(f"[FlowController] CONFIRMING failure! Dropping to IDENTIFYING cascade to re-identify new phase.")
                self.progression_state = "IDENTIFYING"
                # Falls through to _cascade_incorrect below

        self._cascade_incorrect(parent_widget, is_timeout=is_timeout)

    def _cascade_incorrect(self, parent_widget, is_timeout=False):
        """During IDENTIFYING: run the full cascade."""
        current_node = self.get_current_node()

        # Water break side-loop for L1 timeouts
        if is_timeout and current_node == "evaluate_L1":
            print(f"[FlowController] Timeout at {current_node} → Routing to Water Break")
            try:
                from core.navigator import navigator
                navigator.navigate_to("water_break")
            except Exception as e:
                print(f"[FlowController] Routing error: {e}")
            return

        # (Kinesthetic logic was moved to on_incorrect_answer)

        self.cascade_index += 1
        next_node = self.get_current_node()
        print(f"[FlowController] Cascade → {next_node}")

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
        except Exception as e:
            print(f"[FlowController] Routing error: {e}")

    # ── Scaffolding Completion ──

    def advance_cascade(self, parent_widget=None):
        """Called when a scaffolding screen finishes."""
        if self.progression_state == "IDENTIFYING":
            self.cascade_index += 1
            next_node = self.get_current_node()
            print(f"[FlowController] Cascade advancing → {next_node}")
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
            # CONFIRMING/ADVANCING: scaffolding done → evaluate
            if self.progression_state == "ADVANCING":
                phase = self._get_phase_above(self.identified_phase)
            else:
                phase = self.identified_phase
            eval_level = self._get_eval_level(phase) if phase else 1

            phase_to_eval_index = {"none": 0, "engage": 2, "explore": 4, "explain": 6, "elaborate": 8}
            self.cascade_index = phase_to_eval_index.get(phase, 0)

            state_manager.set_affordance_level(eval_level)
            state_manager.current_stage = f"evaluate_L{eval_level}"
            print(f"[FlowController] Scaffolding done → evaluate L{eval_level}")
            try:
                from core.navigator import navigator
                navigator.navigate_to("evaluate")
            except Exception:
                pass

    def kinesthetic_passed(self, parent_widget):
        current_node = self.get_current_node()
        level = int(current_node[-1]) if current_node.startswith("evaluate_L") else state_manager.get_affordance_level()
        print(f"[FlowController] Kinesthetic L{level} passed → retrying {current_node}")
        
        # Telemetry Log
        from core.telemetry_logger import telemetry_logger
        telemetry_logger.log_event("KINESTHETIC_RESULT", detail=f"Passed Kinesthetic at L{level}", is_correct=True)

        state_manager.current_stage = current_node
        try:
            from core.navigator import navigator
            navigator.navigate_to("evaluate")
        except Exception as e:
            print(f"[FlowController] Error: {e}")

    def kinesthetic_failed(self, parent_widget):
        current_node = self.get_current_node()
        level = int(current_node[-1]) if current_node.startswith("evaluate_L") else state_manager.get_affordance_level()
        print(f"[FlowController] Kinesthetic L{level} failed | State: {self.progression_state}")
        
        # Telemetry Log
        from core.telemetry_logger import telemetry_logger
        telemetry_logger.log_event("KINESTHETIC_RESULT", detail=f"Failed Kinesthetic at L{level}", is_correct=False)

        if self.progression_state != "IDENTIFYING":
            self.baseline_confirms = 0
            if self.progression_state == "ADVANCING":
                # Failed to move up — revert to CONFIRMING at baseline phase
                self.progression_state = "CONFIRMING"
                student_name = state_manager.get_current_student() or "unknown"
                print(f"[FlowController] ADVANCING kinesthetic failure. Reverting to baseline phase '{self.identified_phase}'. Moving to next student.")
                self._save_student_state(student_name)
                import core.session_logic as session_logic
                session_logic.next_student()
                return
            elif self.progression_state == "CONFIRMING":
                # Failed baseline — drop to cascade to re-identify
                print(f"[FlowController] CONFIRMING kinesthetic failure! Dropping to IDENTIFYING cascade to re-identify new phase.")
                self.progression_state = "IDENTIFYING"
                # Falls through to _cascade_incorrect below

        print("[FlowController] Dropping to next scaffolding phase")
        self._cascade_incorrect(parent_widget)

    # ── Timeout / Skip / Break ──

    def on_timeout(self, parent_widget):
        self.on_incorrect_answer(parent_widget, is_timeout=True)

    def on_skip(self, parent_widget):
        """Skip the current student without saving any data. Re-add them to the end of the queue."""
        current_node = self.get_current_node()
        student_name = state_manager.get_current_student() or "unknown"
        print(f"[FlowController] Skip at: {current_node} | Student: {student_name} — NO data saved, re-queuing.")
        
        # Telemetry Log
        from core.telemetry_logger import telemetry_logger
        telemetry_logger.log_event("USER_SKIP", detail=f"Skipped at {current_node}")

        get_robot_eyes().set_expression("sad")

        # Re-add the student to the END of the queue so they are called again
        queue = state_manager.get_student_queue()
        if student_name not in queue:
            queue.append(student_name)
            state_manager.set_student_queue(queue)
            print(f"[FlowController] Re-queued '{student_name}' at end of queue. Queue: {queue}")

        # Reset path for this student (no data saved)
        if hasattr(state_manager, 'current_path'):
            state_manager.current_path = []

        import core.session_logic as session_logic
        session_logic.next_student()

    def on_break(self, parent_widget):
        print(f"[FlowController] Rabbit Break at: {self.get_current_node()}")
        get_robot_eyes().set_expression("sleeping")
        try:
            from core.navigator import navigator
            navigator.navigate_to("break")
        except Exception:
            pass

    def on_water_break(self, parent_widget):
        print(f"[FlowController] Water Break at: {self.get_current_node()}")
        get_robot_eyes().set_expression("sleeping")
        try:
            from core.navigator import navigator
            navigator.navigate_to("water_break")
        except Exception:
            pass

    def resume_cascade(self, parent_widget):
        current_node = self.get_current_node()
        get_robot_eyes().set_expression("default")
        print(f"[FlowController] Resuming at: {current_node}")
        try:
            from core.navigator import navigator
            nav_target = SCREEN_MAP.get(current_node)
            if nav_target:
                navigator.navigate_to(nav_target)
        except Exception as e:
            print(f"[FlowController] Resume error: {e}")


flow_controller = FlowController()
