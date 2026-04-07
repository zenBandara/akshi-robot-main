class StateManager:
    def __init__(self):
        # Current UI screen state
        self._current_screen = "idle"
        
        # Session state
        self._current_session_id = None
        self._selected_teacher = None
        self._current_student = None
        self._student_list = []
        self._student_queue = []
        
        # Task state
        self._current_task = None
        self._affordance_level = 1
        self._five_e_stage = "evaluate"

    # Session ID Tracking
    def get_current_session(self):
        return self._current_session_id
        
    def set_current_session(self, session_id):
        self._current_session_id = session_id

    # Screen State
    def get_current_screen(self):
        return self._current_screen
        
    def set_current_screen(self, screen_name):
        self._current_screen = screen_name

    # Teacher
    def get_selected_teacher(self):
        return self._selected_teacher
        
    def set_selected_teacher(self, teacher):
        self._selected_teacher = teacher

    # Student
    def get_current_student(self):
        return self._current_student
        
    def set_current_student(self, student):
        self._current_student = student

    def get_student_list(self):
        return self._student_list

    def set_student_list(self, students):
        self._student_list = students

    def get_student_queue(self):
        return self._student_queue

    def set_student_queue(self, queue):
        self._student_queue = queue

    # Task & Affordance
    def get_current_task(self):
        return self._current_task
        
    def set_current_task(self, task):
        self._current_task = task

    def get_affordance_level(self):
        return self._affordance_level
        
    def set_affordance_level(self, level):
        self._affordance_level = level

    def get_five_e_stage(self):
        return self._five_e_stage
        
    def set_five_e_stage(self, stage):
        self._five_e_stage = stage

# Global singleton instance
state_manager = StateManager()
