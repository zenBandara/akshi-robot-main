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
    
    # 1.5 Student States (Persistent Memory) table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_states (
        student_name TEXT PRIMARY KEY,
        progression_state TEXT,
        identified_phase TEXT,
        baseline_confirms INTEGER
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
        used_kinesthetic INTEGER DEFAULT 0,
        teacher_intervention INTEGER DEFAULT 0,
        timestamp TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
    ''')
    
    # ── Auto-Migration: Add missing columns ──
    try:
        cursor.execute("SELECT used_kinesthetic FROM student_metrics LIMIT 1")
    except sqlite3.OperationalError:
        print("[Database] Migrating student_metrics: Adding used_kinesthetic column...")
        cursor.execute("ALTER TABLE student_metrics ADD COLUMN used_kinesthetic INTEGER DEFAULT 0")

    try:
        cursor.execute("SELECT teacher_intervention FROM student_metrics LIMIT 1")
    except sqlite3.OperationalError:
        print("[Database] Migrating student_metrics: Adding teacher_intervention column...")
        cursor.execute("ALTER TABLE student_metrics ADD COLUMN teacher_intervention INTEGER DEFAULT 0")
    
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

def log_student_metric(session_id, student_name, evaluation_passed, method_used, used_kinesthetic=0, teacher_intervention=0):
    """
    Called intimately by flow_controller whenever the Cascade completes or fails fully.
    """
    now_str = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO student_metrics (session_id, student_name, evaluation_passed, method_used, used_kinesthetic, teacher_intervention, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (str(session_id), str(student_name), str(evaluation_passed), str(method_used), int(used_kinesthetic), int(teacher_intervention), now_str))
    conn.commit()
    conn.close()
    print(f"[RL Telemetry Logged] Student:{student_name} | Passed:{evaluation_passed} | Method:{method_used} | Kinesthetic:{used_kinesthetic} | TeacherIntervention:{teacher_intervention}")

def get_student_optimal_starting_method(student_name):
    """
    Inteligently fetches the historical behavioral success metric for the specified student.
    Returns structurally: (method_used, evaluation_passed, used_kinesthetic)
    Returns (None, None, 0) natively if no history officially exists.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT method_used, evaluation_passed, used_kinesthetic
        FROM student_metrics 
        WHERE student_name = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''', (str(student_name),))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0], row[1], row[2]
    return None, None, 0

def update_student_phase(session_id, student_name, new_phase, used_kinesthetic=0, teacher_intervention=0):
    """
    Called when a student is promoted to a new phase during the advancement staircase.
    Logs a new metric entry with the promoted phase as the method_used.
    """
    now_str = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO student_metrics (session_id, student_name, evaluation_passed, method_used, used_kinesthetic, teacher_intervention, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (str(session_id), str(student_name), "promoted", str(new_phase), int(used_kinesthetic), int(teacher_intervention), now_str))
    conn.commit()
    conn.close()
    print(f"[RL Telemetry] PHASE PROMOTION: Student:{student_name} promoted to phase: {new_phase} | Kinesthetic:{used_kinesthetic} | TeacherIntervention:{teacher_intervention}")

def save_student_state(student_name, state, phase, confirms):
    """Saves the student's progression state permanently to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO student_states (student_name, progression_state, identified_phase, baseline_confirms)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(student_name) DO UPDATE SET
            progression_state=excluded.progression_state,
            identified_phase=excluded.identified_phase,
            baseline_confirms=excluded.baseline_confirms
    ''', (str(student_name), str(state), str(phase), int(confirms)))
    conn.commit()
    conn.close()
    print(f"[Database] Permanent State Saved: {student_name} -> [{state} | {phase} | {confirms}]")

def load_student_state(student_name):
    """Loads the student's progression state from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT progression_state, identified_phase, baseline_confirms
        FROM student_states WHERE student_name = ?
    ''', (str(student_name),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0], row[1], row[2]
    return None

# Immediately initialize the DB upon module import securely
init_db()
