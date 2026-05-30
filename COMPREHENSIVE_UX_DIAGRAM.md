# Akshi Robot: Comprehensive User Experience (UX) Diagram

This document outlines the complete, end-to-end user experience and logical flow of the Akshi Robot during a standard classroom session. It is designed to be easily presented and explains exactly how the robot dynamically reacts to teachers and students.

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
        ADAPTIVE --> |Loads Affordance L1/L2/L3| EXPLORE[Explore / Engage / Kinesthetic]
        EXPLORE --> EVAL[Evaluate Screen]
        
        EVAL --> |Answers Correctly| CELEB[Celebration Screen]
        
        EVAL --> |Answers Incorrectly| KINESTHETIC[Kinesthetic Side-Loop]
        KINESTHETIC --> |Try Again| EVAL
        
        EVAL --> |Repeated Failure| TEACHER_INT[Teacher Intervention]
        TEACHER_INT --> CELEB
        
        EVAL --> |Inactivity Timeout| BREAK[Brain/Water Break]
        BREAK --> |Refreshed| EVAL
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
    class TS,IDLE,FETCH,GREET,TASK_INTRO,ADAPTIVE,KINESTHETIC,TEACHER_INT,BREAK,REMINDER,SESS_COMP processNode;
    class FIRST_CHECK,WAIT_BYE,QUEUE_CHECK conditionNode;
    class SCALL,CALIB,EXPLORE,EVAL,CELEB,GOODBYE studentNode;
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
*   **The Lesson:** The student enters the **Constructivist Journey**, interacting with explore/engage screens based on their specific affordance level (L1, L2, or L3).
*   **Evaluation:** The robot tests the student.
    *   *Correct:* Immediate celebration!
    *   *Incorrect:* The robot provides a kinesthetic side-loop to help them learn, or calls the teacher if they are truly stuck.
*   **Handoff:** The robot praises the student on the **Goodbye Screen** and waits for the student to say "Bye". If they forget, it gently reminds them every 20 seconds. 

### 4. Queue Management & Reset
Once the student says "Bye", the robot checks its internal queue. If there are more students, it immediately calls the next name. If the entire class has finished the lesson, the robot goes to the **Session Complete Screen**, cheers for 10 seconds, and automatically puts itself back to sleep on the **Idle Screen** until the next lesson.