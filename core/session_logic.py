from core.state_manager import state_manager
from core.navigator import navigator

# ── TOGGLE FOR TESTING ──
# Set to True: If Firebase has ANY task, the session will loop indefinitely (useful for testing with only 1 task).
# Set to False (Production): The session will ONLY restart if the teacher has selected a DIFFERENT task.
LOOP_SAME_TASK_IN_TESTING = False

def next_student():
    """Pick the next student from the queue. If all students are done, advance to next task round."""
    # End the current student's analytics session (analytics client saves on end_session).
    # Only send if we previously started one for this student.
    if state_manager.is_analytics_session_active():
        import json
        try:
            with open("ginglu-the-robot/calibration_command.json", "w") as f:
                json.dump({"type": "end_session"}, f)
            state_manager.set_analytics_session_active(False)
            print("[Session Logic] Student session ended via IPC.")

            # Telemetry Log
            from core.telemetry_logger import telemetry_logger
            student_name = state_manager.get_current_student() or "unknown"
            telemetry_logger.log_event("STUDENT_SESSION_END", detail=f"Session ended for {student_name}")
        except Exception as e:
            print(f"[Session Logic] IPC end_session error: {e}")

    queue = state_manager.get_student_queue()
    
    if not queue:
        print("[Session Logic] All students complete. Re-checking Firebase for next round...")
        
        try:
            from core import firebase
            import random
            import core.task_loader as task_loader
            
            selected_teacher = state_manager.get_selected_teacher()
            lesson_id = firebase.get_current_lesson(selected_teacher) if selected_teacher else None
            
            if lesson_id:
                # Production check: ensure the new lesson is actually different from the one we just did
                current_task = state_manager.get_current_task()
                current_task_id = current_task.get("task_id") if current_task else None
                
                if not LOOP_SAME_TASK_IN_TESTING and lesson_id == current_task_id:
                    print(f"[Session Logic] Task '{lesson_id}' is the same as the current one. Ending session.")
                    # Falls through to the 'Session Complete' screen below
                else:
                    print(f"[Session Logic] Round Complete. Starting new round for task '{lesson_id}'.")
                
                # 1. Refetch students
                students = firebase.get_students(selected_teacher)
                state_manager.set_student_list(students)
                new_queue = students.copy()
                random.shuffle(new_queue)
                state_manager.set_student_queue(new_queue)
                state_manager.has_shown_task_intro = False
                
                # 2. Load the task
                all_tasks = task_loader.get_loaded_tasks()
                lesson_data = next((t for t in all_tasks if t.get("task_id") == lesson_id), None)
                state_manager.set_current_task(lesson_data)
                
                # 3. Recursively call next_student to pick the first person from the new queue
                return next_student()
            else:
                print("[Session Logic] Firebase returned no lesson. Ending session.")
        except Exception as e:
            print(f"[Session Logic] Error during Firebase re-poll: {e}")

        # If no lesson or error, truly complete the session
        print("[Session Logic] All students complete for this task!")
        
        # Telemetry Log
        from core.telemetry_logger import telemetry_logger
        telemetry_logger.log_event("SESSION_COMPLETE", detail="All students in queue complete")

        navigator.navigate_to("session_complete")
        return
        
    student = queue.pop(0)
    state_manager.set_student_queue(queue)
    state_manager.set_current_student(student)
    
    print(f"Next student selected: {student}")
    
    # First student gets the task introduction screen
    if not getattr(state_manager, 'has_shown_task_intro', False):
        state_manager.has_shown_task_intro = True
        navigator.navigate_to("task_intro")
    else:
        navigator.navigate_to("student_call")

def start_student_questions():
    """Called after calibration. Kicks off the flow_controller's adaptive progression."""
    from core.flow_controller import flow_controller
    student_name = state_manager.get_current_student() or "unknown"
    print(f"[Session Logic] Starting adaptive flow for: {student_name}")
    
    # Telemetry Log
    from core.telemetry_logger import telemetry_logger
    telemetry_logger.log_event("STUDENT_SESSION_START", detail=f"Adaptive flow started for {student_name}")

    flow_controller.start_student_flow(student_name)
