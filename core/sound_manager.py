import os
import pygame

class SoundManager:
    """Centralized asynchronous generic audio engine isolating PyGame initialization logic."""
    def __init__(self):
        self.is_initialized = False
        self.active_bgm = None
        self.sounds = {}
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.is_initialized = True
            
            # Pre-load native audio paths globally mapping fallback endpoints cleanly
            base_dir = os.path.dirname(os.path.dirname(__file__))
            self.sound_paths = {
                "bell": os.path.join(base_dir, "assets", "sounds", "bell.wav"),
                "arcade": os.path.join(base_dir, "assets", "sounds", "arcade_bgm.wav"),
                "correct": os.path.join(base_dir, "assets", "sounds", "correct.wav"),
                "incorrect": os.path.join(base_dir, "assets", "sounds", "incorrect.wav"),
                "celebration": os.path.join(base_dir, "assets", "sounds", "celebration.wav")
            }
        except Exception as e:
            print(f"[SoundManager] Critical Failure initializing PyGame audio driver: {e}")

    def _play_sound(self, name, volume=1.0):
        if not self.is_initialized: return
        path = self.sound_paths.get(name)
        if path and os.path.exists(path):
            try:
                # Cache the sound object in memory to prevent gc deletion while playing async natively
                if name not in self.sounds:
                    self.sounds[name] = pygame.mixer.Sound(path)
                sound = self.sounds[name]
                sound.set_volume(volume)
                sound.play()
            except Exception as e:
                print(f"[SoundManager] Failed to play physical sound {name}: {e}")
                
    def play_bell(self, volume=0.4):
        self._play_sound("bell", volume)
        
    def play_correct(self, volume=0.6):
        self._play_sound("correct", volume)
        
    def play_incorrect(self, volume=0.6):
        self._play_sound("incorrect", volume)
        
    def play_celebration(self, volume=0.6):
        self._play_sound("celebration", volume)

    def play_bgm(self, name="arcade", volume=0.15):
        if not self.is_initialized: return
        self.stop_bgm()
        
        path = self.sound_paths.get(name)
        if path and os.path.exists(path):
            try:
                if name not in self.sounds:
                    self.sounds[name] = pygame.mixer.Sound(path)
                self.active_bgm = self.sounds[name]
                self.active_bgm.set_volume(volume)
                self.active_bgm.play(loops=-1)
            except Exception:
                pass
                
    def stop_bgm(self):
        """Immediately interrupt global active background loops securely."""
        if self.active_bgm:
            try:
                self.active_bgm.stop()
            except Exception: pass
            self.active_bgm = None
            
    def stop_all(self):
        """Emergency mute executing explicit physical hardware overrides."""
        if self.is_initialized:
            pygame.mixer.stop()
            self.active_bgm = None

# Global hardware wrapper mapping
sound_manager = SoundManager()
