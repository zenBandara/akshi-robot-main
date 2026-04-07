import sqlite3
import os
import uuid
import datetime

# Setup paths dynamically based on root
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
data_dir = os.path.join(project_root, "data")
db_path = os.path.join(data_dir, "telemetry.db")

def init_db():
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        teacher_id TEXT,
        created_at TEXT
    )
    ''')
    
    # 2. Student Telemetry (RL Metrics) table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        student_name TEXT,
        evaluation_passed TEXT,
        method_used TEXT,
        timestamp TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("[Database] SQLite initialized and mapping schema safely secured.")

def start_session(teacher_id):
    """
    Creates a fundamentally unique session referencing the authenticated teacher.
    Returns the session ID so it can be cached in the state manager.
    """
    session_id = str(uuid.uuid4())
    now_str = datetime.datetime.now().isoformat()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sessions (session_id, teacher_id, created_at) VALUES (?, ?, ?)',
                   (session_id, teacher_id, now_str))
    conn.commit()
    conn.close()
    print(f"[Database] Started new RL loop session ID {session_id} for teacher {teacher_id}")
    return session_id

def log_student_metric(session_id, student_name, evaluation_passed, method_used):
    """
    Called intimately by flow_controller whenever the Cascade completes or fails fully.
    """
    now_str = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO student_metrics (session_id, student_name, evaluation_passed, method_used, timestamp)
    VALUES (?, ?, ?, ?, ?)
    ''', (str(session_id), str(student_name), str(evaluation_passed), str(method_used), now_str))
    conn.commit()
    conn.close()
    print(f"[RL Telemetry Logged] Student:{student_name} | Passed:{evaluation_passed} | Method:{method_used}")

# Immediately initialize the DB upon module import securely
init_db()
