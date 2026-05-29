# Robot Eye Expressions: Student Journey Report

This document outlines exactly **when** and **why** the physical robot's eyes change their expression throughout a standard student session. It maps the events in the application (like greeting, congratulating, or failing) to the physical hardware expressions (`Happy`, `Sad`, `Cheer`, `Lovely`).

## 1. Session Start & Greeting
*   **When the robot first greets the student:** The eyes change to **Lovely** (warm & affectionate) to make the student feel welcome.
*   **After the greeting finishes:** The eyes reset to **Happy** (default state) while waiting for the next action.

## 2. The Calibration Game (Magical Eyes)
*   **When starting the calibration:** The eyes change to **Cheer** to build excitement for the mini-game.
*   **During instructions (e.g., "Look over here!"):** The eyes change to **Lovely** (curious/surprised) to capture the child's attention.
*   **When calibration is successfully completed:** The eyes reset to **Happy**, indicating the robot is ready to begin the real lesson.

## 3. Introducing New Tasks
*   **When introducing a fun new learning task:** The eyes change to **Lovely** (wide-eyed/surprised) to build anticipation before the task starts.
*   **Once the intro finishes:** The eyes return to **Happy**.

## 4. During the Lesson (Explore, Engage, Kinesthetic)
*   **When asking a question or waiting for an action:** The eyes are **Happy**.
*   **When cheering the student on during an active task:** The eyes change to **Cheer** to keep the student's energy up.

## 5. Evaluation & Answers
*   **When the robot is evaluating an answer:** The eyes revert to **Happy** (thinking mode).
*   **When the student answers CORRECTLY:** The eyes change to **Cheer** to celebrate their success and reinforce positive learning.
*   **When the student answers INCORRECTLY:** The eyes change to **Sad** to show gentle empathy ("Oh no, that's okay, let's try again").

## 6. Calling the Teacher (Intervention)
*   **When the student struggles and the robot calls the teacher:** The eyes change to **Sad**, indicating that the robot itself needs help to assist the student.
*   **When the teacher arrives and helps:** The eyes change back to **Cheer** or **Happy** to resume the lesson positively.

## 7. Celebrations & Rewards
*   **When a major milestone or the session is completed:** The eyes start at **Lovely** (surprised excitement) and quickly transition to **Cheer** as the robot formally congratulates the student on an amazing job.

## 8. Taking Breaks (Water Break / Rest)
*   **When the robot suggests taking a rest or a water break:** The eyes change to **Happy** (simulating a resting/sleeping state) so as not to demand attention while the student rests.

## 9. Saying Goodbye
*   **When the session ends and it's time to say goodbye:** The eyes change to **Cheer** (encouraging) as it tells the student they did an amazing job and asks them to say "Bye".
*   **When the student successfully says "Bye":** The eyes reset to **Happy** as the robot prepares to call the next student in line.

## 10. Hardware Safety (Face Tracking)
*   **If the student runs away or the camera loses their face:** The eyes automatically change to **Sad** and the robot says *"I can't see you!"*
*   **When the student returns to the camera frame:** The eyes immediately change to **Happy** and the robot says *"I can see you!"*