import asyncio
import edge_tts
import os
import threading
import hashlib
import pygame


class VoiceManager:

    def __init__(self):
        self.voice = "en-IN-NeerjaNeural"
        self.pitch = "+4Hz"
        self.audio_folder = "voice_cache"

        os.makedirs(self.audio_folder, exist_ok=True)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except: pass

    async def generate_voice(self, text, filename, rate):

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=rate,
            pitch=self.pitch
        )

        await communicate.save(filename)

    def speak(self, text, audio_name, rate="+10%"):
        # Synthesize a short deterministic hash of the text to invalidate legacy caches when JSON changes natively
        text_hash = hashlib.md5(text.encode()).hexdigest()[:6]
        filename = os.path.join(self.audio_folder, f"{audio_name}_{text_hash}.mp3")

        if os.path.exists(filename):
            print("Using cached audio:", filename)
        else:
            print("Generating audio:", filename)
            asyncio.run(self.generate_voice(text, filename, rate))

        def play():
            try:
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"Error playing sound: {e}")
                
        threading.Thread(target=play, daemon=True).start()

    def stop(self):
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass