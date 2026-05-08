"""
Dummy Firebase — uses the REAL serviceAccountKey.json so data flows
to the same Firebase Realtime Database the robot would use.

Searches for the key in multiple locations:
  1. ../serviceAccountKey.json  (project root)
  2. ./serviceAccountKey.json   (dummyBackend/ itself)

If no key is found, gracefully degrades — everything still works
locally, just no Firebase writes.
"""

import os
import socket

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_KEY_CANDIDATES = [
    os.path.join(_THIS_DIR, "..", "serviceAccountKey.json"),   # project root
    os.path.join(_THIS_DIR, "serviceAccountKey.json"),         # inside dummyBackend/
]

_KEY_PATH = None
for candidate in _KEY_CANDIDATES:
    if os.path.exists(candidate):
        _KEY_PATH = os.path.abspath(candidate)
        break

_firebase_ok = False

if _KEY_PATH is None:
    print("[DummyFirebase] ⚠️  serviceAccountKey.json NOT found — Firebase disabled")
else:
    try:
        import firebase_admin
        from firebase_admin import credentials, db

        cred = credentials.Certificate(_KEY_PATH)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://ginglu-robot-default-rtdb.firebaseio.com"
        })
        _firebase_ok = True
        print(f"[DummyFirebase] ✅ Firebase initialized (key: {_KEY_PATH})")
    except Exception as e:
        print(f"[DummyFirebase] ⚠️  Firebase init failed: {e}")


def update_connected_ip():
    """Push the local IP to Firebase so the server can find us."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"

    if _firebase_ok:
        try:
            from firebase_admin import db
            db.reference("connected_ip").set(ip)
            print(f"[DummyFirebase] Connected IP updated: {ip}")
        except Exception as e:
            print(f"[DummyFirebase] Failed to update IP: {e}")
    else:
        print(f"[DummyFirebase] (no Firebase) Local IP is: {ip}")

    return ip


def get_connected_ip():
    """Read the connected IP from Firebase (used by server to connect)."""
    if _firebase_ok:
        try:
            from firebase_admin import db
            ip = db.reference("connected_ip").get()
            if ip:
                return ip
        except Exception:
            pass
    return "127.0.0.1"
