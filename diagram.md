# Ginglu Robot: Comprehensive User Flow & Adaptive Logic

This diagram illustrates the end-to-end journey of a student interacting with the Ginglu robot, including the adaptive 5E learning model, data persistence, and the multi-stage verification algorithm.

```mermaid
graph TD
    %% 1. Session Initialization
    Start((Student Arrives)) --> CheckDB{Check SQLite DB}
    
    subgraph "Phase 1: Session Initialization"
        CheckDB -- "New Student" --> State_Ident[State: IDENTIFYING]
        CheckDB -- "History Found" --> State_Conf[State: CONFIRMING]
        State_Conf --> LoadPhase[Load Historical Optimal Phase]
    end

    %% 2. The Core Interaction Loop (Adaptive Flow)
    subgraph "Phase 2: The Adaptive Learning Loop (5E Model)"
        direction TB
        
        %% Identifying Cascade
        State_Ident --> EvalL1[Evaluate Level 1: 4 Options]
        
        %% Kinesthetic Loop
        EvalL1 -- "Wrong Answer" --> Kinesthetic[Kinesthetic Loop: Brain Break]
        Kinesthetic -- "Pass" --> EvalL1
        Kinesthetic -- "Fail" --> Engage[Engage: Educational Video]
        
        %% Scaffolding Cascade
        Engage --> EvalL2[Evaluate Level 2: 2 Options]
        EvalL2 -- "Fail" --> Explore[Explore: Activity]
        Explore --> EvalL3a[Evaluate Level 3: 1 Focal Object]
        EvalL3a -- "Fail" --> Explain[Explain: Simplification]
        Explain --> EvalL3b[Evaluate Level 3]
        EvalL3b -- "Fail" --> Elaborate[Elaborate: Scaffolding]
        Elaborate --> EvalL3c[Evaluate Level 3]
        
        EvalL3c -- "Fail" --> Teacher[Teacher Intervention]
    end

    %% 3. The 2-Stage Verification & Advancement
    subgraph "Phase 3: Verification & Promotion"
        %% Success Logic
        EvalL1 -- "Correct" --> Verify_Ident[Identify Phase that Helped]
        EvalL2 -- "Correct" --> Verify_Ident
        EvalL3a -- "Correct" --> Verify_Ident
        EvalL3b -- "Correct" --> Verify_Ident
        EvalL3c -- "Correct" --> Verify_Ident
        
        Verify_Ident --> SaveID[Save to DB: Identified Phase]
        SaveID --> Switch_Conf[Switch to State: CONFIRMING]
        
        %% Confirming Logic (2-Stage Verification)
        Switch_Conf --> Conf1[Confirm Round 1]
        Conf1 -- "Correct" --> Conf2[Confirm Round 2]
        Conf1 -- "Wrong" --> Reset_Conf[Reset Confirm Counter]
        
        %% Advancing Logic
        Conf2 -- "Correct" --> Switch_Adv[Switch to State: ADVANCING]
        Switch_Adv --> TryHarder[Try Phase Above Optimal]
        
        TryHarder -- "Correct" --> Promote[Save to DB: Promoted Phase]
        TryHarder -- "Wrong" --> Fallback[Fallback to CONFIRMING]
    end

    %% 4. Data Persistence
    subgraph "Data & Persistence Model"
        SaveID -- "Action" --> DB_Insert[(SQLite: student_metrics)]
        Promote -- "Action" --> DB_Insert
        DB_Insert -- "Record" --> SessionID[Session ID]
        DB_Insert -- "Record" --> StudentName[Student Name]
        DB_Insert -- "Record" --> Method[Method/Phase Used]
        DB_Insert -- "Record" --> Result[Result: Pass/Promoted]
    end

    %% Completion
    Next((Next Student))
    Celebrate[Celebration Screen] --> Next
    Teacher --> Next
    Promote --> Celebrate
    Conf1 -- "Correct" --> Celebrate
    Reset_Conf --> Next
    Fallback --> Next
```

## Detailed System Logic Breakdown

### 1. Identifying the "Optimal Phase"
When a **New Student** starts, the robot enters the `IDENTIFYING` state. It runs the **5E Cascade**:
*   The robot starts at the hardest level (`Evaluate L1`).
*   If the student fails, it provides more support (Engage → Explore → Explain → Elaborate).
*   The moment the student answers correctly, the robot **Identifies** which support phase was active.
*   **Database Action:** This "Identified Phase" is saved to the SQLite `student_metrics` table as the student's new baseline.

### 2. Two-Stage Verification (`CONFIRMING`)
Once a phase is identified, the robot doesn't immediately try to make the task harder. It must first **Verify** mastery.
*   The student enters the `CONFIRMING` state.
*   The student must answer **2 consecutive questions correctly** at their identified phase in future rounds.
*   If they fail any of these two "Confirmation Rounds," the counter resets to zero, and they stay at that level.

### 3. The Advancement Staircase (`ADVANCING`)
After passing the 2-stage verification, the robot attempts to **Promote** the student.
*   The robot enters the `ADVANCING` state.
*   It serves a task using the **Phase Above** their current optimal one (e.g., if they were at `Engage`, it tries `None/Level 1`).
*   **Success:** If they pass, the new, harder phase is saved to the database as their optimal method.
*   **Failure:** If they fail, the robot realizes they aren't ready to move up and falls back to the `CONFIRMING` state for their previous level.

### 4. Returning Student Logic (Reusing Data)
When a student returns (`start_student_flow`):
1.  The `FlowController` queries the SQLite database for the student's last recorded `method_used`.
2.  If found, the robot **Skips the Identifying Cascade**.
3.  It immediately routes the student to their **Optimal Phase** and sets the state to `CONFIRMING`.
4.  This ensures the robot "remembers" exactly how much help each specific child needs.

### 5. The Kinesthetic "Brain Break"
Regardless of the student's history, the **first failure at any level** triggers the Kinesthetic loop. 
*   This is a physical reset (e.g., "Jump like a frog").
*   If they pass the physical game, they get **one retry** at the current evaluation.
*   If they fail the physical game, they drop to the next scaffolding phase (in `IDENTIFYING` state) or rotate to the next student (in `CONFIRMING` state).
