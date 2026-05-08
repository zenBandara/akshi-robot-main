# Firebase & Local Task Architecture in Ginglu Robot

This document explains the data pipeline between the remote Firebase Realtime Database and the local PySide6 Python application. It details how the robot dynamically fetches students, handles sessions, and matches them with local curriculum data (the 5E JSON tasks).

---

## 1. Firebase Initialization & Connection
The connection is managed in `core/firebase.py`. 
- The application uses the `firebase_admin` SDK.
- It authenticates securely using a local `serviceAccountKey.json` credential file.
- It connects to the Firebase Realtime Database (`https://ginglu-robot-default-rtdb.firebaseio.com`) for active session synchronization and student data, and sets up a stub for Firestore to log metrics (handled in Phase 6).

---

## 2. Fetching Teachers and Students
When the application launches (or during the setup phase), it needs to know who is in the classroom today.

1. **Teacher Selection (`get_teachers`)**: The app queries the `/teachers` node to retrieve a list of available teacher profiles.
2. **Student Attendance (`get_students`)**: Once a teacher is selected (e.g., "Mr. Smith"), the system queries `/teachers/{teacher_key}/attendance`.
   - It searches for today's date (formatted as `YYYY-MM-DD`).
   - **Fallback Mechanism**: If no attendance is found for today, it gracefully falls back to the most recently submitted attendance record.
   - The data is expected as a comma-separated string (e.g., `"Alice, Bob, Charlie"`), which is split and parsed into a local Python list.

---

## 3. Session and Queue Management
Once the student list is fetched from Firebase, it is handed over to the local state management.

- **State Manager (`core/state_manager.py`)**: The list of students is saved into the `_student_list` and copied into a working `_student_queue`.
- **Session Logic (`core/session_logic.py`)**: The system pops one student at a time from this queue. The active student is set as the `_current_student`.
- **Flow Controller (`core/flow_controller.py`)**: The active student is then passed into the dynamic 5E evaluation pipeline. The robot determines whether the student needs to go through the **"IDENTIFYING"** cascade (for new students) or if they are returning and should start in a **"CONFIRMING/ADVANCING"** state based on historical database records.

---

## 4. How Tasks Are Handled and Matched
While student data comes dynamically from Firebase, the actual **educational content (Tasks)** is stored locally to ensure ultra-fast, offline-capable asset loading (images, videos, TTS).

1. **Local Task JSONs**: Tasks are stored in `Tasks/task_jsons/` (e.g., `t_1.json`, `t_2.json`).
2. **Schema Validation**: When the session starts, `core/task_loader.py` scans this directory. It strictly validates every JSON file to ensure it has all required 5E stages (`engage`, `explore`, `explain`, `elaborate`, `evaluate`) and necessary fields (`speech_start`, `multiple_choices_word`, etc.).
3. **Task Queueing**: `build_task_queue()` reads the valid local JSON tasks and sorts them sequentially by their `task_id` (e.g., `t_1` → `t_2` → `t_3`).
4. **Firebase Override (Current Lesson)**: The `get_current_lesson(teacher_key)` function in Firebase allows the teacher to remotely set the starting point (e.g., forcing the robot to start at `t_3`). If set, the local application uses this ID to align the local JSON queue with the teacher's remote curriculum choice.

### Summary of the Flow:
1. **Firebase** tells the local app *who* is in the classroom (Students).
2. **Firebase** tells the local app *what* they should be learning today (Current Lesson ID).
3. **Local `task_loader.py`** finds the matching JSON file on the hard drive (e.g., `t_1.json`).
4. **Local `flow_controller.py`** guides the student through that specific JSON data using the adaptive 5E phase scaffolding.
5. Once the task is completed (or failed), the results are logged back to Firebase, and the next student in the queue is called up to the robot.
