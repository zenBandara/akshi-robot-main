import firebase_admin
from firebase_admin import credentials, db
import json

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://akshi-robot-default-rtdb.firebaseio.com"
})

def fetch_raw_data():
    root_ref = db.reference("/")
    all_data = root_ref.get()
    
    # Save to a file for easier inspection
    with open("firebase_dump.json", "w") as f:
        json.dump(all_data, f, indent=2)
    
    print("Firebase data dumped to firebase_dump.json")

if __name__ == "__main__":
    fetch_raw_data()
