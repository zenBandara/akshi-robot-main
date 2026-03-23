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
    """Fetch the student list for the specified teacher."""
    ref = db.reference(f"teachers/{teacher_key}/students")
    data = ref.get()
    
    if isinstance(data, dict):
        return list(data.keys())
    elif isinstance(data, list):
        return data
        
    return []

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