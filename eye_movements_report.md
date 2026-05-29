# Robot Eye Expressions: Student Journey Report

This document outlines exactly **when** and **why** the physical robot's eyes change their expression throughout a standard student session. It maps the events in the application (like greeting, congratulating, or failing) to the physical hardware expressions (`Happy`, `Sad`, `Cheer`, `Lovely`).

*Note: Based on recent feedback, eye expressions have been heavily optimized to minimize distraction during core learning tasks.*

## 1. Session Start & Greeting
*   **When the robot first greets the student:** The eyes change to **Lovely** (warm & affectionate) to make the student feel welcome.
*   **After the greeting finishes (Idle/Waiting):** The eyes reset to **Happy** (default state).
*   **Calling the next person screen:** The eyes remain **Happy**.

## 2. The Calibration Game (Magical Eyes)
*   **During the entire calibration phase:** The eyes remain completely **Happy** to prevent distractions while tracking is established.
*   **Successfully eyes calibrated:** The eyes change to **Lovely** to celebrate the locked tracking state.

## 3. During the Lesson (Explore, Engage, Kinesthetic & Constructivist)
*   **All Constructivist and Kinesthetic Screens:** The eyes are locked to **Happy** for the entirety of these phases. This ensures the student is not distracted by changing eye patterns while trying to focus on learning and movement tasks.

## 4. Evaluation & Answers
*   **Incorrectly answered the problem:** The eyes remain **Happy** to keep the interaction positive and undistracting. 
*   **Successfully answered the problem (Cheer Window):** The eyes change to **Cheer** to celebrate their success and reinforce positive learning.
*   **After loading the next screen:** The eyes reset to **Happy**.

## 5. Saying Goodbye
*   **After saying bye (Goodbye screen active):** The eyes change to **Lovely** (affectionate) as it tells the student they did an amazing job.
*   **Loading the next screen:** The eyes reset to **Happy** as the robot prepares to call the next student in line.

## 6. Hardware Safety (Face Tracking)
*   **If the student runs away or the camera loses their face:** The eyes automatically change to **Sad** and the robot says *"I can't see you!"*
*   **When the student returns to the camera frame:** The eyes immediately change to **Happy** and the robot says *"I can see you!"*