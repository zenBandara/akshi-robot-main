# Student Cognitive Improvement Model (Vygotsky's Scaffolding)

This document maps out the algorithm the robot uses to track, adapt to, and actively improve a student's cognitive independence across multiple sessions. This is powered by an SQLite database that securely remembers the student's cognitive state across days and weeks.

## The Cognitive Scaffolding Ladder
The robot ranks the scaffolding it provides from highest support to lowest support. As the student improves, the robot actively *removes* scaffolding to build their independence.

1.  **`elaborate`** (Maximum Scaffolding / Affordance L3)
2.  **`explain`** (High Scaffolding / Affordance L3)
3.  **`explore`** (Moderate Scaffolding / Affordance L3)
4.  **`engage`** (Low Scaffolding / Affordance L2)
5.  **`none`** (Zero Scaffolding / Direct Evaluation L1)

---

## The Dynamic Progression Algorithm

```mermaid
graph TD
    START([Student Session Starts]) --> LOAD_DB
    
    subgraph Database Loading
        direction LR
        LOAD_DB[Check SQLite DB]
        LOAD_DB --> |Returning Student| FOUND[State Found]
        LOAD_DB --> |Brand New| NOT_FOUND[No Record Found]
    end
    
    NOT_FOUND --> IDENTIFYING
    FOUND --> CONFIRMING
    FOUND --> ADVANCING
    
    subgraph IDENTIFYING STATE
        direction TB
        CASCADE[Scaffolding Cascade<br/>Starts at 'none', moves down]
        CASCADE --> |Answer Correct| IDENTIFY_PASS[Baseline Phase Set<br/>Confirms = 0]
    end
    
    IDENTIFY_PASS --> CONFIRMING
    
    subgraph CONFIRMING STATE
        direction TB
        ASK_BASE[Ask Question at Baseline Phase]
        
        ASK_BASE --> |Answer Correct| CONFIRM_PASS[Confirms + 1]
        ASK_BASE --> |Answer Incorrect| CONFIRM_FAIL[Kinesthetic Failed<br/>Lost Baseline]
    end
    
    CONFIRM_PASS --> |Confirms = 1| CONFIRMING
    CONFIRM_PASS --> |Confirms = 2| ADVANCING
    CONFIRM_FAIL --> IDENTIFYING
    
    subgraph ADVANCING STATE
        direction TB
        ASK_HARDER[Ask Question at 1 Phase Higher<br/>Less Scaffolding]
        
        ASK_HARDER --> |Answer Correct| ADVANCE_PASS[Promoted! Baseline Updates]
        ASK_HARDER --> |Answer Incorrect| ADVANCE_FAIL[Reverts to old Baseline]
    end
    
    ADVANCE_PASS --> CONFIRMING
    ADVANCE_FAIL --> CONFIRMING
    
    CONFIRMING -.-> |Session Ends| SAVE_DB[(Save to SQLite)]
    ADVANCING -.-> |Session Ends| SAVE_DB
```

---

## Detailed Example: How a Student Improves

Let's walk through an example of a student named **Leo** interacting with the robot across multiple rounds/days.

1.  **Round 1 (Identifying):** 
    Leo is a brand new student. The robot starts with no scaffolding (`none`). Leo fails. The robot adds support (`engage`). Leo fails. The robot adds more support (`explore`). Leo gets it right!
    *   **Action:** The database saves Leo's baseline phase as `explore`. The state becomes **CONFIRMING**.

2.  **Round 2 (Confirming - Day 1):** 
    The robot loads Leo's profile. Since he is in the **CONFIRMING** state, it gives him a task at the `explore` phase. Leo gets it right.
    *   **Action:** `baseline_confirms` becomes `1/2`.

3.  **Round 3 (Confirming - Day 2):** 
    The robot gives Leo another task at the `explore` phase. Leo gets it right again.
    *   **Action:** `baseline_confirms` hits `2/2`. Leo has proven mastery of this level! His state is upgraded to **ADVANCING**.

4.  **Round 4 (Advancing - Day 3):** 
    Because Leo is **ADVANCING**, the robot intentionally *removes* a layer of scaffolding. It gives him a harder task at the `engage` phase (1 level higher than `explore`).
    *   *Scenario A (Success):* Leo gets it right! He is officially **Promoted**. His new baseline becomes `engage`, and he drops back to **CONFIRMING** (0/2) to master this new level.
    *   *Scenario B (Failure):* Leo gets it wrong. That's okay! He just isn't ready for reduced scaffolding yet. The robot drops his state back to **CONFIRMING** at his old `explore` baseline to give him more practice next time.