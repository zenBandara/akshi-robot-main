import firebase_admin
from firebase_admin import credentials, db
import json

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://akshi-robot-default-rtdb.firebaseio.com"
})

def fetch_data():
    print("Fetching all teachers and students...")
    root_ref = db.reference("/")
    all_data = root_ref.get()
    
    if not all_data:
        print("No data found in Firebase.")
        return

    teachers = all_data.get("teachers", {})
    students_at_root = all_data.get("students", {})
    
    print(f"Number of teachers: {len(teachers)}")
    
    for t_key, t_data in teachers.items():
        print(f"\nTeacher Key: {t_key}")
        # Sometimes keys are sanitized emails (replace . with _)
        # If t_data is a dict, it might have email
        if isinstance(t_data, dict):
            email = t_data.get("email", "N/A")
            name = t_data.get("name", "N/A")
            print(f"  Name: {name}, Email: {email}")
            
            # Look for students under teacher
            # The code said students are in 'attendance' as comma-separated string
            attendance = t_data.get("attendance", {})
            if attendance:
                print("  Students found in attendance records:")
                all_student_names = set()
                for date, names_str in attendance.items():
                    if isinstance(names_str, str):
                        names = [s.strip() for s in names_str.split(",") if s.strip()]
                        all_student_names.update(names)
                
                for s_name in sorted(all_student_names):
                    # Check if this student exists in students_at_root to get email
                    s_info = students_at_root.get(s_name, {})
                    s_email = "Unknown Email"
                    if isinstance(s_info, dict):
                        s_email = s_info.get("email", "Unknown Email")
                    elif isinstance(s_info, str):
                        # Maybe students_at_root[s_name] is the email itself?
                        s_email = s_info
                        
                    print(f"    - {s_name} ({s_email})")
            else:
                print("  No attendance records found for this teacher.")
        else:
            print(f"  Data: {t_data}")

if __name__ == "__main__":
    fetch_data()
