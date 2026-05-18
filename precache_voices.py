import os
import json
import glob
import hashlib
import asyncio
from core.voice_manager import VoiceManager
from core.dialogue import DialoguePool
try:
    from core import firebase
except ImportError:
    firebase = None

def extract_speech(data, speech_list):
    if isinstance(data, dict):
        for key, value in data.items():
            if 'speech' in key and isinstance(value, str):
                speech_list.append(value)
            elif isinstance(value, dict):
                extract_speech(value, speech_list)
            elif isinstance(value, list):
                for item in value:
                    extract_speech(item, speech_list)
    elif isinstance(data, list):
        for item in data:
            extract_speech(item, speech_list)

def main():
    print("Starting Voice Pre-Cacher...")
    vm = VoiceManager()
    tasks_dir = os.path.join("Tasks", "task_jsons")
    all_speech = []
    
    # Pre-cache student names from Firebase
    if firebase:
        print("Fetching students from Firebase to precache names...")
        try:
            teachers = firebase.get_teachers()
            all_students = set()
            for t in teachers:
                all_students.update(firebase.get_students(t))
            
            for student in all_students:
                vm.ensure_name_cached(student)
        except Exception as e:
            print("Could not fetch students from Firebase:", e)
    else:
        print("Firebase module not found. Skipping student name precaching.")

    # Pre-cache DialoguePool template segments
    print("Pre-caching DialoguePool templates...")
    pools = [
        DialoguePool.CORRECT, DialoguePool.INCORRECT_L1, DialoguePool.INCORRECT_L2,
        DialoguePool.INCORRECT_L3, DialoguePool.TIMEOUT, DialoguePool.MOTIVATION_NUDGE,
        DialoguePool.MOTIVATION_NUDGE_L2, DialoguePool.MOTIVATION_NUDGE_L3, DialoguePool.SKIP_L3,
        DialoguePool.BREAK_STORY, DialoguePool.BREAK_RETURN, DialoguePool.BREAK_HURRY,
        DialoguePool.WAITING_THINKING
    ]
    for pool in pools:
        for template in pool:
            # We add dummy name formatting just so we can extract prefix and suffix
            # or we just let speak_with_name handle the generation and immediately stop
            # Actually, it's easier to just split by {name} and add to all_speech
            parts = template.split("{name}")
            for part in parts:
                cleaned = part.strip()
                if cleaned:
                    all_speech.append(cleaned)
                    
    # Also add standard static templates from screens
    all_speech.extend([
        "can you please come on up? It is your turn to shine!",
        "Hey", "I think you need some energy! Let's do something super fun!",
        "That's okay", "I think you might need a little rest!",
        "it looks like you could use a small break!",
        "Great hopping,", "You're halfway there! Keep going!",
        "Almost done,", "Hop back to your seat!",
        "Oh no,", "didn't come back. Let's move on to the next friend!",
        "Yay", "welcome back! You're full of energy now! Let's try again!",
        "Let's ask teacher for some help! Don't worry", "you did great trying!"
    ])

    # Static fallback speeches from screens (legacy)
    all_speech.extend([
        "Let's try moving our beautiful bodies! What is the hand that you use for eating?",
        "That is your right hand! Now, can you lift up the hand you use for eating nice and high?",
        "Awesome! Now, what about your other hand? That is your left hand! Can you wiggle your left hand high in the air?",
        "Wow! Now, go over to your teacher and show them your beautiful left and right hands!",
        "Let's review this concept together.",
        "Say 'Done' when you are done.",
        "Let's review this concept together. Say 'Done' when you are done.",
        "Let's try something super fun safely together.",
        "Watch our character carefully on the screen!",
        "Say 'Done' when you are all done!",
        "Let's begin our adventure!",
        "Look closely!",
        "Say 'Done' when you are done!"
    ])

    for json_file in glob.glob(os.path.join(tasks_dir, "*.json")):
        with open(json_file, 'r') as f:
            try:
                data = json.load(f)
                extract_speech(data, all_speech)
                
                # Reconstruct combined speeches from explain screen
                if "explain" in data:
                    e = data["explain"]
                    s_start = e.get("speech_start", "Let's review this concept together.")
                    s_end = e.get("speech_end", "Say 'Done' when you are done.")
                    all_speech.append(f"{s_start} {s_end}")
            except Exception as e:
                print(f"Error reading {json_file}: {e}")

    # Deduplicate
    all_speech = list(set(all_speech))
    print(f"Found {len(all_speech)} unique speech phrases to cache.")
    
    new_files_generated = 0
    
    for i, text in enumerate(all_speech):
        text = text.strip()
        if not text: continue
        
        text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
        filename = os.path.join(vm.audio_folder, f"tts_{text_hash}.mp3")
        
        if not os.path.exists(filename):
            print(f"[{i+1}/{len(all_speech)}] GENERATING: {text[:60]}...")
            asyncio.run(vm.generate_voice(text, filename, "+10%"))
            new_files_generated += 1
        else:
            print(f"[{i+1}/{len(all_speech)}] SKIP (Cached): {text[:60]}...")
            
    print(f"Done! Generated {new_files_generated} new TTS files.")

if __name__ == "__main__":
    main()
