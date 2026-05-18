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
        self.name_cache_folder = os.path.join(self.audio_folder, "names")
        self.combined_cache_folder = os.path.join(self.audio_folder, "combined")

        os.makedirs(self.audio_folder, exist_ok=True)
        os.makedirs(self.name_cache_folder, exist_ok=True)
        os.makedirs(self.combined_cache_folder, exist_ok=True)
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
        # Synthesize a strong deterministic hash of the text
        text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
        # Ignore audio_name for the actual file to prevent duplicates for different students!
        filename = os.path.join(self.audio_folder, f"tts_{text_hash}.mp3")

        if os.path.exists(filename):
            print("Using cached audio:", filename)
        else:
            print("Generating audio:", filename)
            asyncio.run(self.generate_voice(text, filename, rate))
            
        try:
            sound = pygame.mixer.Sound(filename)
            duration_ms = int(sound.get_length() * 1000)
            del sound  # Release the Sound object immediately to avoid channel conflicts
        except Exception as e:
            print("Could not get duration natively, falling back to estimation.", e)
            words_count = len(text.split())
            duration_ms = max(2000, int((words_count / 1.8) * 1000))

        # Stop any currently playing audio first to prevent overlap/stutter
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass
            
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
        
        return duration_ms

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NEW: Name-Based Audio Concatenation System
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def ensure_name_cached(self, name, rate="+10%"):
        """Generate and cache a student name as standalone audio if not already cached.
        
        Args:
            name: Student name, e.g. "Dinujaya"
            rate: TTS speech rate
            
        Returns:
            Path to the cached name audio file
        """
        safe_name = name.strip().replace(" ", "_")
        name_file = os.path.join(self.name_cache_folder, f"name_{safe_name}.mp3")
        
        if not os.path.exists(name_file):
            print(f"[VoiceManager] Generating name audio for '{name}' → {name_file}")
            asyncio.run(self.generate_voice(name, name_file, rate))
        else:
            print(f"[VoiceManager] Name audio cached: {name_file}")
            
        return name_file

    def speak_with_name(self, template, name, audio_label, rate="+10%"):
        """Speak a template containing {name} by concatenating cached audio segments.
        
        Instead of generating the full text for every student, this method:
        1. Splits the template at {name} into prefix and suffix
        2. Generates/caches audio for the name (once per student)
        3. Generates/caches audio for prefix and suffix (reusable across all students)
        4. Concatenates prefix + name + suffix into a combined file
        5. Plays the combined file
        
        Falls back to full TTS generation if concatenation fails.
        
        Args:
            template: Speech text with {name} placeholder, e.g. "Hey {name}, you're amazing!"
            name: Student name, e.g. "Dinujaya"
            audio_label: Label for logging, e.g. "celebrate_Dinujaya"
            rate: TTS speech rate
            
        Returns:
            Duration in milliseconds
        """
        # If template doesn't contain {name}, just use regular speak
        if "{name}" not in template:
            full_text = template
            return self.speak(full_text, audio_label, rate)
        
        try:
            # 1. Split template into segments around {name}
            parts = template.split("{name}")
            prefix = parts[0].strip() if parts[0].strip() else ""
            suffix = parts[1].strip() if len(parts) > 1 and parts[1].strip() else ""
            
            # 2. Build a unique combined cache key from (template + name)
            combined_hash = hashlib.md5(f"{template}|{name}".encode()).hexdigest()[:12]
            combined_file = os.path.join(self.combined_cache_folder, f"combined_{combined_hash}.mp3")
            
            # 3. Check if combined file already exists
            if os.path.exists(combined_file):
                print(f"[VoiceManager] Using cached combined audio: {combined_file}")
                return self._play_file(combined_file, template.replace("{name}", name))
            
            # 4. Ensure all segments are cached
            segment_files = []
            
            # Prefix segment
            if prefix:
                prefix_hash = hashlib.md5(prefix.encode()).hexdigest()[:10]
                prefix_file = os.path.join(self.audio_folder, f"tts_{prefix_hash}.mp3")
                if not os.path.exists(prefix_file):
                    print(f"[VoiceManager] Generating prefix audio: '{prefix[:50]}...'")
                    asyncio.run(self.generate_voice(prefix, prefix_file, rate))
                segment_files.append(prefix_file)
            
            # Name segment
            name_file = self.ensure_name_cached(name, rate)
            segment_files.append(name_file)
            
            # Suffix segment
            if suffix:
                suffix_hash = hashlib.md5(suffix.encode()).hexdigest()[:10]
                suffix_file = os.path.join(self.audio_folder, f"tts_{suffix_hash}.mp3")
                if not os.path.exists(suffix_file):
                    print(f"[VoiceManager] Generating suffix audio: '{suffix[:50]}...'")
                    asyncio.run(self.generate_voice(suffix, suffix_file, rate))
                segment_files.append(suffix_file)
            
            # 5. Concatenate all segments
            self._concatenate_segments(segment_files, combined_file)
            print(f"[VoiceManager] Combined audio saved: {combined_file}")
            
            # 6. Play the combined file
            return self._play_file(combined_file, template.replace("{name}", name))
            
        except Exception as e:
            # FALLBACK: If anything goes wrong, regenerate the full text via TTS
            print(f"[VoiceManager] Concatenation failed ({e}), falling back to full TTS generation")
            full_text = template.replace("{name}", name)
            return self.speak(full_text, audio_label, rate)

    def _concatenate_segments(self, segment_files, output_path):
        """Concatenate multiple MP3 files using raw binary concatenation.
        
        MP3 is a frame-based format, so simply appending the raw bytes of 
        multiple MP3 files produces a valid MP3 stream that plays correctly.
        
        Args:
            segment_files: List of paths to MP3 files to concatenate
            output_path: Path to write the combined MP3 file
        """
        with open(output_path, 'wb') as outfile:
            for segment_path in segment_files:
                if os.path.exists(segment_path):
                    with open(segment_path, 'rb') as infile:
                        outfile.write(infile.read())
                else:
                    print(f"[VoiceManager] Warning: Segment file not found: {segment_path}")

    def _play_file(self, filename, text_for_estimation=""):
        """Play an audio file and return its duration in milliseconds.
        
        Args:
            filename: Path to the MP3 file to play
            text_for_estimation: Original text for duration estimation fallback
            
        Returns:
            Duration in milliseconds
        """
        try:
            sound = pygame.mixer.Sound(filename)
            duration_ms = int(sound.get_length() * 1000)
            del sound
        except Exception as e:
            print("Could not get duration natively, falling back to estimation.", e)
            words_count = len(text_for_estimation.split()) if text_for_estimation else 10
            duration_ms = max(2000, int((words_count / 1.8) * 1000))

        # Stop any currently playing audio first to prevent overlap/stutter
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass
            
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
        
        return duration_ms

    def stop(self):
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass