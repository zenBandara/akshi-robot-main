# Akshi Robot: Comprehensive User Experience (UX) Diagram

This document outlines the complete, end-to-end user experience and logical flow of the Akshi Robot during a standard classroom session. It is designed to be easily presented and explains exactly how the robot dynamically reacts to teachers and students, with a detailed breakdown of the internal Constructivist & Affordance pathways.

## Visual Flowchart

```mermaid
graph TD
    classDef startNode fill:#d8b4e2,stroke:#333,stroke-width:2px,color:black;
    classDef processNode fill:#a3c2f1,stroke:#333,stroke-width:2px,color:black;
    classDef conditionNode fill:#fce8b2,stroke:#333,stroke-width:2px,color:black;
    classDef studentNode fill:#b8e0b6,stroke:#333,stroke-width:2px,color:black;

    START([App Launch]) --> TS[Teacher Selection Screen]
    TS --> |Teacher Selects Profile| IDLE[Idle Screen / Resting]
    
    IDLE --> |Teacher Triggers WAKE| FETCH[Fetch Firebase Data]
    FETCH --> |Loads Students & Task| GREET[Greeting Screen]
    
    GREET --> FIRST_CHECK{Is this the first<br/>student in queue?}
    FIRST_CHECK -->|Yes| TASK_INTRO[Task Intro Screen]
    TASK_INTRO --> SCALL[Student Call Screen]
    FIRST_CHECK -->|No| SCALL
    
    SCALL --> |Calls Student by Name| CALIB[Calibration Screen]
    CALIB --> |Magical Eyes Minigame| ADAPTIVE[Adaptive Learning Flow]
    
    subgraph Constructivist Educational Journey
        direction TB
        ADAPTIVE --> ROUTER{Determine Student's<br/>Affordance Level}
        
        %% Affordance Level 1
        ROUTER --> |Affordance Level 1<br/>Basic Assessment| L1_PATH[No Scaffolding Required]
        L1_PATH --> EVAL_L1[Evaluate Screen - L1]
        
        %% Affordance Level 2
        ROUTER --> |Affordance Level 2<br/>Medium Cognitive Support| L2_PATH[Engage Screen]
        L2_PATH --> EVAL_L2[Evaluate Screen - L2]
        
        %% Affordance Level 3
        ROUTER --> |Affordance Level 3<br/>High Cognitive Support| L3_PATH[Explore / Explain / Elaborate]
        L3_PATH --> EVAL_L3[Evaluate Screen - L3<br/>*Speech Speed -10%*]
        
        %% Merge Evaluation Results
        EVAL_L1 --> EVAL_MERGE{Evaluation Result}
        EVAL_L2 --> EVAL_MERGE
        EVAL_L3 --> EVAL_MERGE
        
        EVAL_MERGE --> |Answers Correctly| CELEB[Celebration Screen]
        
        EVAL_MERGE --> |Answers Incorrectly| KINESTHETIC[Kinesthetic Side-Loop]
        KINESTHETIC --> |Try Again| ROUTER
        
        EVAL_MERGE --> |Repeated Failure| TEACHER_INT[Teacher Intervention]
        TEACHER_INT --> CELEB
        
        EVAL_MERGE --> |Inactivity Timeout| BREAK[Brain/Water Break]
        BREAK --> |Refreshed| ROUTER
    end
    
    CELEB --> GOODBYE[Goodbye Screen]
    GOODBYE --> |Robot says 'Bye!'| WAIT_BYE{Student says 'BYE'?}
    
    WAIT_BYE --> |Timeout 20s| REMINDER[Reminder Voice Prompt]
    REMINDER --> WAIT_BYE
    
    WAIT_BYE --> |'BYE' Command Received| QUEUE_CHECK{Are there more<br/>students in queue?}
    
    QUEUE_CHECK --> |Yes| SCALL
    QUEUE_CHECK --> |No| SESS_COMP[Session Complete Screen]
    
    SESS_COMP --> |Waits exactly 10 Seconds| IDLE

    class START startNode;
    class TS,IDLE,FETCH,GREET,TASK_INTRO,ADAPTIVE,L1_PATH,L2_PATH,L3_PATH,KINESTHETIC,TEACHER_INT,BREAK,REMINDER,SESS_COMP processNode;
    class FIRST_CHECK,WAIT_BYE,QUEUE_CHECK,ROUTER,EVAL_MERGE conditionNode;
    class SCALL,CALIB,EVAL_L1,EVAL_L2,EVAL_L3,CELEB,GOODBYE studentNode;
```

---

## Step-by-Step Explanation for Presentation

### 1. Startup & Standby
When the robot is turned on, the teacher selects their profile on the **Teacher Selection Screen**. The robot immediately goes to sleep on the **Idle Screen**, waiting patiently so it doesn't interrupt the classroom.

### 2. Waking & Fetching
When the teacher is ready, they trigger the `WAKE` command. The robot connects to Firebase, downloads the newest lesson plan, shuffles the list of students, and transitions to the **Greeting Screen** to say hello to the class.

### 3. The Student Loop
*   **Task Intro & Calling:** If it's the very first student, the robot explains the rules of the game (**Task Intro**). It then calls the specific student's name to come forward (**Student Call**).
*   **Calibration:** The robot plays a "Magical Eyes" game to lock its camera onto the student's face.
*   **The Constructivist Journey (Adaptive Routing):** The robot dynamically determines the student's needs and routes them to the correct Affordance Level:
    *   **Level 1:** Directly evaluates the student with no scaffolding.
    *   **Level 2:** The student interacts with the **Engage Screen** before being evaluated.
    *   **Level 3:** The student receives maximum cognitive support, moving through the **Explore, Explain, and Elaborate Screens**. During evaluation, the robot's speaking speed is slowed down by 10% to ensure high comprehension.
*   **Evaluation Outcomes:**
    *   *Correct:* Immediate transition to the Celebration Screen.
    *   *Incorrect:* The robot launches a **Kinesthetic Side-Loop** (physical movement break) to help them reset before trying again.
    *   *Repeated Failure:* The robot triggers **Teacher Intervention**.
*   **Handoff:** The robot praises the student on the **Goodbye Screen** and waits for the student to say "Bye". If they forget, it gently reminds them every 20 seconds. 

### 4. Queue Management & Reset
Once the student says "Bye", the robot checks its internal queue. If there are more students, it immediately calls the next name. If the entire class has finished the lesson, the robot goes to the **Session Complete Screen**, cheers for 10 seconds, and automatically puts itself back to sleep on the **Idle Screen** until the next lesson.