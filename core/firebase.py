import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred,{
    "databaseURL":"https://akshi-robot-default-rtdb.firebaseio.com"
})

def get_teachers():

    ref = db.reference("teachers")
    data = ref.get()

    if data:
        return list(data.keys())

    return []


def get_teacher_data(email):

    ref = db.reference(f"teachers/{email}")
    return ref.get()