from core.state_manager import state_manager
from core.navigator import navigator

def next_student():
    """Pick the next student from the queue and proceed to the Student Calling Screen."""
    # End the current student's WebSocket session before moving on
    import json
    try:
        with open("akshi-the-robot/calibration_command.json", "w") as f:
            json.dump({"type": "end_session"}, f)
        print("[Session Logic] Student session ended via IPC.")
    except Exception as e:
        print(f"[Session Logic] IPC end_session error: {e}")

    # Stop the backend face-tracking subprocess (releases camera for next student)
    from core import backend_manager
    backend_manager.stop()

    queue = state_manager.get_student_queue()
    
    if not queue:
        print("Session Complete! No more students.")
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
    queue = state_manager.get_student_queue()
    is_first_student = (len(queue) == len(student_list) - 1) if student_list else True
    
    if is_first_student:
        navigator.navigate_to("task_intro")
    else:
        navigator.navigate_to("student_call")
