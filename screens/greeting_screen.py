import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect

from core.state_manager import state_manager
from core.voice_manager import VoiceManager
from core.navigator import navigator

window = None
voice_manager = VoiceManager()
title_opacity = None
subtitle_opacity = None
anim_1 = None
anim_2 = None

def get_ui():
    global window
    current_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(current_dir)
    ui_path = os.path.join(project_root, "ui", "greetingUI.ui")

    loader = QUiLoader()
    file = QFile(ui_path)
    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", ui_path)
        return None

    window = loader.load(file)
    file.close()

    def on_show_hook():
        print("[Greeting Screen] Becoming active with Cinematic Typography...")
        state_manager.set_current_screen("greeting")
        
        from core.keyboard_manager import keyboard_manager
        keyboard_manager.unregister_handler() # Prevent W spamming
        
        # Sequester initial opacity to functionally invisible
        global title_opacity, subtitle_opacity
        title_opacity = QGraphicsOpacityEffect(window.title_label)
        window.title_label.setGraphicsEffect(title_opacity)
        title_opacity.setOpacity(0.0)
        
        subtitle_opacity = QGraphicsOpacityEffect(window.subtitle_label)
        window.subtitle_label.setGraphicsEffect(subtitle_opacity)
        subtitle_opacity.setOpacity(0.0)
        
        # Run animations & voice async after UI flips natively
        QTimer.singleShot(100, on_ready)

    window.on_show = on_show_hook
    return window

def on_ready():
    global anim_1, anim_2
    
    greeting_message = "Hello there! I am Ginglu! Ready to learn something fun today?"
    print(f"[Robot Speaks]: {greeting_message}")
    
    # 1. Animate massive Deep Blue Title
    anim_1 = QPropertyAnimation(title_opacity, b"opacity")
    anim_1.setDuration(1200)
    anim_1.setStartValue(0.0)
    anim_1.setEndValue(1.0)
    anim_1.setEasingCurve(QEasingCurve.OutCubic)
    anim_1.start()
    
    # 2. Animate secondary delayed Soft Subtitle 
    anim_2 = QPropertyAnimation(subtitle_opacity, b"opacity")
    anim_2.setDuration(1500)
    anim_2.setStartValue(0.0)
    anim_2.setEndValue(1.0)
    anim_2.setEasingCurve(QEasingCurve.OutCubic)
    QTimer.singleShot(800, anim_2.start) # Execute exactly synchronized visually trailing title
    
    # Speak the greeting
    duration_ms = 3000
    try:
        duration_ms = voice_manager.speak(greeting_message, "greeting_message")
    except Exception as e:
        print("VoiceManager error (ignoring for now):", e)

    # Wait exactly for exact length, then transition to the first student
    QTimer.singleShot(duration_ms, transition_to_first_student)

def transition_to_first_student():
    print("Transitioning to first student...")
    import core.session_logic as session_logic
    session_logic.next_student()
