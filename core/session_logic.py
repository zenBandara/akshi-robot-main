from core.state_manager import state_manager
from core.navigator import navigator

def next_student():
    """Pick the next student from the queue. If all students are done, advance to next task round."""
    # End the current student's WebSocket session
    import json
    try:
        with open("akshi-the-robot/calibration_command.json", "w") as f:
            json.dump({"type": "end_session"}, f)
        print("[Session Logic] Student session ended via IPC.")
    except Exception as e:
        print(f"[Session Logic] IPC end_session error: {e}")

    queue = state_manager.get_student_queue()
    
    if not queue:
        # All students finished this round — try advancing to next task
        task_queue = state_manager.get_task_queue()
        
        if task_queue:
            # More tasks available! Start a new round
            next_task = task_queue.pop(0)
            state_manager.set_task_queue(task_queue)
            state_manager.set_current_task(next_task)
            print(f"[Session Logic] ── NEW ROUND ── Task: {next_task.get('task_id')} | Remaining: {len(task_queue)}")
            
            # Reload the full student list for this new round
            all_students = state_manager.get_student_list()
            if all_students:
                new_queue = all_students.copy()
                student = new_queue.pop(0)
                state_manager.set_student_queue(new_queue)
                state_manager.set_current_student(student)
                
                state_manager.set_five_e_stage("evaluate")
                state_manager.set_affordance_level(1)
                
                print(f"[Session Logic] Round starting with student: {student}")
                navigator.navigate_to("student_call")
            else:
                navigator.navigate_to("session_complete")
        else:
            # No more tasks — session is truly complete
            print("[Session Logic] All tasks and students complete!")
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
