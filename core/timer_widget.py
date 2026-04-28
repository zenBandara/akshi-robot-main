from PySide6.QtCore import QTimer, QPropertyAnimation, QObject
from PySide6.QtWidgets import QGraphicsOpacityEffect

class EmojiTimerWidget(QObject):
    def __init__(self, label_widget, total_seconds=20, clock_count=10, timeout_callback=None, progress_callback=None):
        super().__init__()
        self.label_widget = label_widget
        self.total_seconds = total_seconds
        self.clock_count = clock_count
        self.remaining_clocks = clock_count
        self.timeout_callback = timeout_callback
        self.progress_callback = progress_callback
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._trigger_fade)
        
        self.fade_effect = QGraphicsOpacityEffect(self.label_widget)
        self.label_widget.setGraphicsEffect(self.fade_effect)
        
        self.fade_anim = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_anim.setDuration(350)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.15)
        self.fade_anim.finished.connect(self._remove_clock)
        
        self._update_display()
        
    def start(self):
        self.remaining_clocks = self.clock_count
        self._update_display()
        
        # Calculate interval for fading out one single clock instance
        interval = int((self.total_seconds / self.clock_count) * 1000)
        self.timer.start(interval)
        
    def stop(self):
        self.timer.stop()
        self.fade_anim.stop()
        self.fade_effect.setOpacity(1.0)
        
    def _update_display(self):
        self.label_widget.setText(" ".join(["🕒"] * self.remaining_clocks))
        self.fade_effect.setOpacity(1.0)
        
    def _trigger_fade(self):
        if self.remaining_clocks <= 0:
            self.stop()
            if self.timeout_callback:
                self.timeout_callback()
            return
            
        try:
            from core.sound_manager import sound_manager
            sound_manager.play_tick()
        except ImportError: pass
            
        self.fade_anim.start()
        
    def _remove_clock(self):
        self.remaining_clocks -= 1
        self._update_display()

        if self.progress_callback:
            progress = self.remaining_clocks / self.clock_count if self.clock_count > 0 else 0.0
            self.progress_callback(progress)
        
        if self.remaining_clocks <= 0:
            self.stop()
            if self.timeout_callback:
                self.timeout_callback()
