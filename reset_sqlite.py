#!/usr/bin/env python3
"""
🧹 Reset SQLite Telemetry Data
================================
Clears ALL student metrics and session data from the local SQLite database.
Does NOT touch Firebase data.

Usage:
    python reset_sqlite.py
"""

import sqlite3
import os

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
db_path = os.path.join(data_dir, "telemetry.db")

def reset():
    if not os.path.exists(db_path):
        print("❌ No database found at:", db_path)
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Show what we're about to delete
    cursor.execute("SELECT COUNT(*) FROM sessions")
    session_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM student_metrics")
    metric_count = cursor.fetchone()[0]

    print(f"📊 Current data: {session_count} sessions, {metric_count} student metrics")

    # Delete all rows (keeps tables intact)
    cursor.execute("DELETE FROM student_metrics")
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()

    print(f"✅ Cleared {metric_count} student metrics and {session_count} sessions.")
    print("🔥 Firebase data is untouched.")
    print("🚀 Ready for a fresh start!")

if __name__ == "__main__":
    reset()
