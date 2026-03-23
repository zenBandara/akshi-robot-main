import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred,{
    "databaseURL":"https://akshi-robot-default-rtdb.firebaseio.com"
})

# Initialize Firestore for logging
try:
    firestore_client = firestore.client()
except ValueError:
    firestore_client = None
    print("Warning: Firestore client could not be initialized.")

def get_teachers():

    ref = db.reference("teachers")
    data = ref.get()

    if data:
        return list(data.keys())

    return []


def get_teacher_data(email):

    ref = db.reference(f"teachers/{email}")
    return ref.get()

def get_students(teacher_key):
    """Fetch today's student list for the specified teacher."""
    today_str = datetime.date.today().isoformat()
    
    ref = db.reference(f"teachers/{teacher_key}/attendance")
    attendance_data = ref.get()
    
    if not attendance_data or not isinstance(attendance_data, dict):
        return []
        
    # Try today, fallback to the most recently submitted attendance
    if today_str in attendance_data:
        students_str = attendance_data[today_str]
    else:
        latest_date = sorted(attendance_data.keys())[-1]
        students_str = attendance_data[latest_date]
        print(f"Warning: No attendance found for today ({today_str}). Using latest available ({latest_date}).")
        
    if isinstance(students_str, str):
        return [s.strip() for s in students_str.split(",") if s.strip()]
        
    return []

def get_current_lesson(teacher_key):
    """Fetch the active lesson assigned by the teacher."""
    ref = db.reference(f"teachers/{teacher_key}/current_lesson")
    lesson = ref.get()
    return lesson if lesson else "t_1"

def log_event(data):
    """Stub for Firestore logging. Handled in Phase 6."""
    print("[FIRESTORE STUB] Event logged:", data)
    if firestore_client:
        pass

if __name__ == "__main__":
    print("Testing Firebase connection...")
    teachers_list = get_teachers()
    print("Teachers found:", teachers_list)
    if teachers_list:
        for t in teachers_list:
            print(f"Students under '{t}':", get_students(t))