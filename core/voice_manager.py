import asyncio
import edge_tts
import os
import threading
from playsound import playsound


class VoiceManager:

    def __init__(self):
        self.voice = "en-IN-NeerjaNeural"
        self.pitch = "+4Hz"
        self.audio_folder = "voice_cache"

        os.makedirs(self.audio_folder, exist_ok=True)

    async def generate_voice(self, text, filename, rate):

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=rate,
            pitch=self.pitch
        )

        await communicate.save(filename)

    def speak(self, text, audio_name, rate="+10%"):

        filename = os.path.join(self.audio_folder, audio_name + ".mp3")

        if os.path.exists(filename):
            print("Using cached audio:", filename)
        else:
            print("Generating audio:", filename)
            asyncio.run(self.generate_voice(text, filename, rate))

        def play():
            try:
                playsound(filename)
            except Exception as e:
                print(f"Error playing sound: {e}")
                
        threading.Thread(target=play, daemon=True).start()