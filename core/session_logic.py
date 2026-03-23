from core.state_manager import state_manager
from core.navigator import navigator

def next_student():
    """Pick the next student from the queue and proceed to the Student Calling Screen."""
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
    navigator.navigate_to("student_call")
