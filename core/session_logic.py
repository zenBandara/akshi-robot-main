from core.state_manager import state_manager
from core.navigator import navigator

def next_student():
    """Pick the next student from the queue. If all students are done, advance to next task round."""
    # End the current student's WebSocket session
    import json
    try:
        with open("ginglu-the-robot/calibration_command.json", "w") as f:
            json.dump({"type": "end_session"}, f)
        print("[Session Logic] Student session ended via IPC.")
    except Exception as e:
        print(f"[Session Logic] IPC end_session error: {e}")

    queue = state_manager.get_student_queue()
    
    if not queue:
        # ── DEVELOPMENT STAGE LOGIC ──
        # Check Firebase again to see if we should start another round.
        # In Production: We should only repeat if (new_lesson != old_lesson).
        # In Development: We repeat as long as Firebase has ANY lesson information.
        print("[Session Logic] All students complete. Re-checking Firebase for next round...")
        
        try:
            from core import firebase
            import random
            import core.task_loader as task_loader
            
            selected_teacher = state_manager.get_selected_teacher()
            lesson_id = firebase.get_current_lesson(selected_teacher) if selected_teacher else None
            
            if lesson_id:
                print(f"[Session Logic] Round Complete. Firebase has task '{lesson_id}'. Starting another round.")
                
                # 1. Refetch students
                students = firebase.get_students(selected_teacher)
                state_manager.set_student_list(students)
                new_queue = students.copy()
                random.shuffle(new_queue)
                state_manager.set_student_queue(new_queue)
                
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
        navigator.navigate_to("session_complete")
        return
        
    student = queue.pop(0)
    state_manager.set_student_queue(queue)
    state_manager.set_current_student(student)
    
    # Reset tracking state for new student
    state_manager.set_five_e_stage("evaluate")
    state_manager.set_affordance_level(1)
    
    print(f"Next student selected: {student}")
    
    # First student gets the task introduction screen
    student_list = state_manager.get_student_list()
    remaining = state_manager.get_student_queue()
    is_first_student = (len(remaining) == len(student_list) - 1) if student_list else True
    
    if is_first_student:
        navigator.navigate_to("task_intro")
    else:
        navigator.navigate_to("student_call")

def start_student_questions():
    """Called after calibration. Kicks off the flow_controller's adaptive progression."""
    from core.flow_controller import flow_controller
    student_name = state_manager.get_current_student() or "unknown"
    print(f"[Session Logic] Starting adaptive flow for: {student_name}")
    flow_controller.start_student_flow(student_name)
