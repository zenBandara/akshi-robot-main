# Akshi Robot Project Phases

This document outlines the step-by-step development phases for the Akshi humanoid robot software. The system is built using Python and PySide6, incorporates a Firebase backend, and strictly follows a 5E educational model with adaptive Affordance Levels tailored for preschool students.

---

## Phase 1: Foundation & System Setup
**Objective:** Establish the core project architecture, user interface skeleton, and database connectivity.
* **UI Skeleton:** Create the foundational, child-friendly PySide6 Main Window. Prioritize a clean, visually appealing design suited for preschoolers (no touch inputs, large visuals, dynamic expressions).
* **Keyboard Listener:** Implement the global keyboard listener for development interaction (e.g., pressing `W` to wake up the robot).
* **Backend Connection:** Establish and authenticate the Firebase connection. Connect to the Realtime Database (for active sessions/state) and Firestore (for logging).
* **Idle/Wake-up State:** Implement the transition from idle to the greeting state when the wake-up command is triggered.

## Phase 2: Teacher & Student Flow 
**Objective:** Handle user selection and initiate the session.
* **Teacher Selection:** Fetch the list of available teachers from Firebase and display them. Implement keyboard mapping (e.g., `A` for Teacher 1, `B` for Teacher 2) for selection.
* **Student Roster:** Upon teacher selection, fetch the relevant student list.
* **Student Selection & Greeting:** Randomly select a student from the list. Have the robot "call" the student by name and greet them.

## Phase 3: The 5E Core & Level 1 Affordance
**Objective:** Build the task engine and the primary Evaluation loop.
* **Task Engine Setup:** Develop a dynamic JSON parser to read external task files (e.g., `t_1.json`). Ensure tasks are picked randomly for the active student.
* **Evaluate Phase (Level 1 Affordance):** 
  * Present the initial evaluation with **4 options** (Physical/Cognitive Level 1).
  * Listen for the student's answer via keyboard input.
* **Success Path Handling:** If the student answers correctly on the first attempt, trigger positive reinforcement (gamified reward/applause), log the success, and immediately move to the next student.

## Phase 4: Adaptive Flow & Higher Affordance 
**Objective:** Implement the failure cascade and adapt the UI according to Affordance Levels.
* **The 5E Cascade:** Implement the logic flow for incorrect answers: `Evaluate -> Elaborate -> Evaluate -> Explain -> Evaluate -> Explore -> Evaluate -> Engage -> Evaluate`.
* **Level 2 Affordance (Elaboration Loop):**
  * Triggered when the student fails the first Evaluation.
  * Update UI for Level 2: Reduce options from 4 to **2 choices**, increase image sizes, apply a full gaming atmosphere, and add a soft bell audio cue before instructions.
* **Level 3 Affordance (Explain/Explore/Engage Loops):**
  * Triggered on subsequent failures.
  * Update UI for Level 3: Simplify language, slow down speech, display only **1 focal object**, visually highlight the target, and frequently use the child's name to maintain focus.

## Phase 5: Edge Cases & Session Controls
**Objective:** Ensure the system handles interruptions, skips, and extreme failure cases gracefully.
* **Skip Functionality:** Allow the child to skip a question. Record the skip, move to the next student, and ensure the skipped student isn't asked the exact same question immediately upon return.
* **Break Functionality:** Allow the child to take a short break holding their current session state. Do not mark them as "finished."
* **Teacher Intervention:** If the child fails all levels (through the Engage phase), the robot politely calls for the teacher's attention. Pause the session, wait for the teacher to resolve the matter and press a `continue` command to move to the next student.

## Phase 6: Comprehensive Logging & Polish
**Objective:** Finalize the analytics, generate test data, and refine the interface.
* **Firestore Logging:** Finalize detailed logging of every interaction. Capture the student ID, task ID, affordance level reached, chronological path taken (e.g., `Eval1 -> Fail -> Elaborate -> Eval2 -> Pass`), and the number of attempts.
* **Dummy Data Generation:** Write multiple mock JSON task files to robustly test random allocation and the full 5E model flows.
* **UI/UX Polish:** Review all screens against the preschool requirements. Refine animations, colors, and the simulated facial expressions of the robot.
* **Final Walkthrough:** Test the entire system end-to-end to ensure readiness for voice module integration in the subsequent research phase.
