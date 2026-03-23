# Akshi Robot — 5E Task JSON Schema

This document defines the official strictly-enforced JSON structure for all tasks loaded by the Akshi Robot system. Every task must be placed in the `Tasks/task_jsons/` directory and must exactly follow this format.

## Root Object
Every task file represents a single learning objective (e.g., "Left and Right", "Colors").
```json
{
  "task_id": "string (Unique identifier, e.g., 't_1')",
  "task_name": "string (Human-readable name, e.g., 'Left Right Identification')",
  "description": "string (High-level explanation of the task's educational goal)",
  
  "engage": { ... },
  "explore": { ... },
  "explain": { ... },
  "elaborate": { ... },
  "evaluate": { ... }
}
```

## Standard 5E Section Fields
Every 5E stage object (`engage`, `explore`, `explain`, `elaborate`, `evaluate`) **must** include the following standard fields:
- `task_title` (string): The title displayed at the top of the screen.
- `speech_start` (string): The exact dialogue the robot will speak when the screen opens.
- `speech_end` (string): The dialogue the robot will speak at the conclusion of the screen's activity.

For the non-interactive stages (`engage`, `explore`, `explain`), they must additionally include:
- `description` (string): Background notes for teachers or general descriptions of the on-screen activity.

*(Optional)* `video_url` (string): Path to an MP4 video file to play automatically during the stage (e.g., `"tasks/t1/engage_video.mp4"`).
*(Optional)* `activity_description` (string): Instructions specifically for Kinesthetic/Explore activities.

## Task Stages (`elaborate` & `evaluate`)
The `elaborate` and `evaluate` stages are actively interactive. In addition to the standard fields above, they **must** include:
- `task_type` (string): The type of question (currently always `"mcq_image"`).
- `task_description` (string): The specific question asked to the student (e.g., *"Which arrow points right?"*).
- `multiple_choices_word` (object): A dictionary of 4 text labels mapping to `"op1"`, `"op2"`, `"op3"`, `"op4"`.
- `multiple_choices_images` (object): A dictionary of 4 image file paths mapping to `"op1"`, `"op2"`, `"op3"`, `"op4"`.
- `correct_option` (string): The key of the correct answer (e.g., `"op2"`).

*(Note on Affordance Levels: At Level 1, all 4 options are shown. At Levels 2 & 3, the runtime engine will dynamically filter this down to 2 options—the `correct_option` and one randomly selected distractor).*

## Complete Example Schema (`t_2.json`)
```json
{
  "task_id": "t_2",
  "task_name": "Counting Objects",
  "description": "A task to help students practice counting to 4.",

  "engage": {
    "task_title": "Let's Count!",
    "speech_start": "Hello! Do you like counting?",
    "speech_end": "Let's look at some numbers together.",
    "description": "Playing a happy counting song video.",
    "video_url": "tasks/t2/engage.mp4"
  },
  
  "explore": {
    "task_title": "Counting on your fingers",
    "speech_start": "Can you hold up three fingers?",
    "speech_end": "Great job, counting is fun!",
    "description": "Kinesthetic activity counting physical fingers."
  },
  
  "explain": {
    "task_title": "What are numbers?",
    "speech_start": "Numbers tell us how many things we have. One, two, three, four!",
    "speech_end": "Now you know how to count.",
    "description": "Robot visually shows numbers."
  },

  "elaborate": {
    "task_type": "mcq_image",
    "task_title": "Let's practice counting",
    "speech_start": "Let's try counting together.",
    "speech_end": "Excellent counting.",
    "task_description": "Which picture has exactly 2 apples?",
    "multiple_choices_word": {
      "op1": "One Apple",
      "op2": "Two Apples",
      "op3": "Three Apples",
      "op4": "Four Apples"
    },
    "multiple_choices_images": {
      "op1": "tasks/t2/apple_1.png",
      "op2": "tasks/t2/apple_2.png",
      "op3": "tasks/t2/apple_3.png",
      "op4": "tasks/t2/apple_4.png"
    },
    "correct_option": "op2"
  },

  "evaluate": {
    "task_type": "mcq_image",
    "task_title": "Show me what you learned!",
    "speech_start": "Okay, it's your turn to count all by yourself.",
    "speech_end": "You are a math superstar!",
    "task_description": "Which picture has 3 stars?",
    "multiple_choices_word": {
      "op1": "One Star",
      "op2": "Two Stars",
      "op3": "Three Stars",
      "op4": "Four Stars"
    },
    "multiple_choices_images": {
      "op1": "tasks/t2/star_1.png",
      "op2": "tasks/t2/star_2.png",
      "op3": "tasks/t2/star_3.png",
      "op4": "tasks/t2/star_4.png"
    },
    "correct_option": "op3"
  }
}
```
