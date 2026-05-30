#!/usr/bin/env python3
"""
🎙️ Voice Speed Test Script
===========================
Standalone tool to test and compare the robot's speaking speeds.
It demonstrates both the standard +10% speed and the new slower +0% speed.

Usage:
    python test_voice_speed.py
"""

import sys
import os
import time

# Add project root to path so we can import core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.voice_manager import VoiceManager
import pygame

def run_voice_test():
    print("="*50)
    print("🎙️ INITIALIZING VOICE MANAGER TEST")
    print("="*50)
    
    # VoiceManager automatically initializes pygame mixer
    vm = VoiceManager()
    
    text_fast = "Hello! This is the standard snappy speed at plus ten percent, used for level one and two."
    text_slow = "Hello! This is the normal, slower speed at zero percent, specifically designed for level three students."
    
    # ---------------------------------------------------------
    # TEST 1: Fast Speed (+10%)
    # ---------------------------------------------------------
    print("\n▶️ [TEST 1] Generating and playing FAST speed (+10%)")
    duration = vm.speak(text_fast, "test_fast", rate="+10%")
    
    # Pygame plays audio asynchronously, so we wait based on the calculated duration
    time.sleep(duration / 1000.0 + 0.5)
    
    # ---------------------------------------------------------
    # TEST 2: Slow Speed (+0%)
    # ---------------------------------------------------------
    print("\n▶️ [TEST 2] Generating and playing SLOW speed (+0%)")
    duration = vm.speak(text_slow, "test_slow", rate="+0%")
    time.sleep(duration / 1000.0 + 0.5)
    
    # ---------------------------------------------------------
    # TEST 3: Name Concatenation at Slow Speed (+0%)
    # ---------------------------------------------------------
    print("\n▶️ [TEST 3] Testing Name Concatenation System at SLOW speed (+0%)")
    template = "You did an amazing job, {name}! Keep up the great work!"
    duration = vm.speak_with_name(template, "Alice", "test_name_slow", rate="+0%")
    time.sleep(duration / 1000.0 + 0.5)
    
    print("\n" + "="*50)
    print("✅ All voice tests completed successfully!")
    print("Check the 'voice_cache/' folder to see the newly generated files!")
    print("="*50)

    # Cleanly stop pygame
    vm.stop()

if __name__ == "__main__":
    run_voice_test()