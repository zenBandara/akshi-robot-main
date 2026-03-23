# Akshi Robot: Phase 3 Integration Testing Plan

This document outlines the standard physical validation procedures required to certify Phase 3 (The 5E Cognitive Flow Engine).

## Prerequisites
1. Ensure your speakers/headphones are unmuted (you need to verify PyGame audio channels).
2. Launch the application from your terminal: `python main.py`
3. Advance through the Teacher Select -> Student Select -> Greeting screens to load the first active task.

---

### Test 64: Perfect Run (Correct on First Attempt)
**Objective:** Verify standard success resolution routing.
1. **Action:** Wait for the robot to finish speaking its first native prompt.
2. **Action:** Click the physically correct answer card.
3. **Expected State:** 
    - The floating Robot Eyes widget should change to a **Surprised / Happy** `( O_O )` state.
    - You should physically hear the `correct.wav` audio chime.
    - The UI should seamlessly fade into the **Celebration Screen** (Star opacity animations).
    - After 4 seconds, the queue should pop and fade natively back to the Greeting Screen (or Session Complete).

---

### Test 65: Elaborate Recovery (Incorrect L1 -> Correct L2)
**Objective:** Verify affordance escalation from Level 1 to Level 2.
1. **Action:** On the first evaluation, deliberately click an **Incorrect** card.
2. **Expected State 1:** 
    - Robot says an encouraging phrase (e.g., "Let's look closer!").
    - UI fades into the **Elaborate Screen** (Mint green layout).
3. **Action:** Press `ENTER` to exit the Elaborate screen.
4. **Expected State 2:** 
    - **Evaluate Level 2** automatically loads. 
    - *Visuals:* Theme shifts to Dark Navy Blue with 2 simplified answer cards.
    - *Audio:* A bell chimes, and soft Arcade BGM begins playing asynchronously.
5. **Action:** Click the **Correct** answer.
6. **Expected State 3:** BGM halts cleanly, UI transitions directly into Celebration Screen.

---

### Test 66: Explain Recovery (Incorrect L1 -> Incorrect L2 -> Correct L3)
**Objective:** Verify maximum affordance escalation reaching Level 3.
1. **Action:** Intentionally fail Level 1 -> `ENTER` through Elaborate -> Intentionally fail Level 2.
2. **Expected State 1:** UI fades into **Explain Screen** (Calm blue layout).
3. **Action:** Press `ENTER` to exit the Explain screen.
4. **Expected State 2:**
    - **Evaluate Level 3** automatically loads.
    - *Visuals:* Aggressive High-Contrast Black/Yellow. Only the correct card pulses physically.
    - *UI Text:* Includes the child's name + "(Press S to Skip)".
    - *Audio:* Robot speech cadence physically slows down by 30% to maximize accessibility.
5. **Action:** Click the **Correct** answer. 
6. **Expected State 3:** Triggers standard Celebration cascade.

---

### Test 67: Full System Failure Cascade & Teacher Intervention
**Objective:** Verify the extreme limits of the central Flow Controller fallback sequences.
1. **Action:** Intentionally fail Evaluate **L1** -> fail **L2** -> fail **L3**.
2. **Expected State 1:** UI natively loads the **Explore Screen** (Vibrant Pink layout, kinesthetic activity).
3. **Action:** Press `ENTER`.
4. **Expected State 2:** Framework loads Evaluate **L3** again. Deliberately fail it again.
5. **Expected State 3:** UI loads **Engage Screen** (Warm Yellow, emotional recovery). 
6. **Action:** Press `ENTER`.
7. **Expected State 4:** Framework loads Evaluate **L3** a third time. Fail it again.
8. **Expected State 5:** System triggers absolute terminal failure -> **Teacher Intervention Screen** (Calm Blue).
9. **Action:** Observe the screen is completely frozen. The child's standard inputs (1, 2, 3, 4, ENTER) are locked globally.
10. **Action:** As the physical human teacher, press `C` on the keyboard.
11. **Final State:** System breaks the cascade natively, popping the queue cleanly to the Greeting Screen.

---

### Test 68: Level 3 Hardware Skip Mechanic
**Objective:** Verify the execution frame securely terminates when physical bypass vectors are invoked.
1. **Action:** Progress a student until they reach **Evaluate Level 3**.
2. **Action:** Physically press the `S` key on your keyboard.
3. **Expected State:** 
    - All audio engines instantly stop.
    - Path serialization natively logs `"skipped"`.
    - UI elegantly fades directly into the Greeting Screen for the next valid child perfectly skipping the active loop.

---

### Test 69: Non-Destructive Pause/Break Resurgence
**Objective:** Verify the state manager caches historical structural data pointers across memory dumps.
1. **Action:** Reach Evaluate Level 2 (or L3).
2. **Action:** Press the `B` key to trigger a hardware Break.
3. **Expected State 1:**
    - Active timers halt immediately. Audio engines spin down.
    - Floating Robot Eyes physically go to **Sleep** `( -.- )zZ`.
    - Screen fades into the static **Break UI**.
4. **Action:** Wait a few seconds, then press `ENTER` to signal the child's return.
5. **Expected State 2:** The engine pulls the cascade pointer and precisely re-renders the exact same instance layout you paused from simultaneously waking up the robot eyes into their default state.

---

### Test 70: Centralized Timer Penalty Resolution
**Objective:** Certify asynchronous background threading explicitly delegates timeout constraints.
1. **Action:** Reach any Evaluate screen constraint.
2. **Action:** Physically remove your hands from the keyboard and wait exactly **20 Seconds**.
3. **Expected State:**
    - Emoji timer naturally collapses off screen.
    - At precisely 0.0s, the UI interprets the inactivity locally as an explicit logical Failure.
    - Floating Robot Eyes shift into a **Thinking** state `( ˘~˘ )`.
    - Framework automatically escalates exactly into the next visual phase (e.g. Elaborate/Explain) identical to if the child had explicitly guessed incorrectly.
