#!/usr/bin/env python3
"""
🎬 Akshi Robot — Client Demo Launcher
=======================================
Launch any showcase scenario instantly with shortened timers.

Usage:
    python demo.py <scenario_number>

Scenarios:
    1  — Smart Student (L1 correct answer → celebration)
    2  — Calibration Game (3-act mini-game)
    3  — Wrong Answer → Kinesthetic
    4  — 1-Minute Motivation Nudge (shortened to 5s)
    5  — L1 Timeout → Kinesthetic (shortened to 10s)
    6  — 🐰 Rabbit Jump Break (full 3 acts, fast timers)
    7  — Break Return → Retry L2
    8  — Break Auto-Skip (shortened to 15s)
    9  — L3 Auto-Skip (shortened to 10s)
   10  — Teacher Intervention (question + correct answer)
   11  — Full Cascade (fast timers)
   12  — RL Smart Start (pre-seeded DB)
    0  — List all scenarios
"""

import sys
import os
import json

# ── Boot PySide6 BEFORE any screen imports ──
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import QObject, QEvent, Qt, QTimer

app = QApplication(sys.argv)

# Now safe to import screens
from core.state_manager import state_manager
from core.keyboard_manager import keyboard_manager
from core.navigator import navigator

# ── Paths ──
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TASK_JSON = os.path.join(PROJECT_ROOT, "Tasks", "task_jsons", "t_1.json")


def load_dummy_task():
    """Load task t_1 as demo data."""
    with open(TASK_JSON, "r") as f:
        return json.load(f)


def setup_state(student="Nadun", level=1):
    """Pre-populate state_manager with demo data."""
    state_manager.set_current_student(student)
    state_manager.set_current_task(load_dummy_task())
    state_manager.set_affordance_level(level)
    state_manager.set_student_queue(["Vidhura", "Sarith"])
    state_manager.current_path = []
    state_manager.set_current_session("demo-session-001")


def build_app():
    """Create the main window + stack + key listener."""
    main_window = QMainWindow()
    main_window.setWindowTitle("🎬 Akshi Demo")
    main_window.setMinimumSize(900, 700)
    main_window.setFocusPolicy(Qt.StrongFocus)

    stack = QStackedWidget()
    stack.setFocusPolicy(Qt.StrongFocus)
    main_window.setCentralWidget(stack)
    navigator.set_stack(stack)

    # Global key listener
    class GlobalKeyListener(QObject):
        def eventFilter(self, obj, event):
            if event.type() == QEvent.Type.KeyPress:
                keyboard_manager.handle_key_press(event)
                return False
            return super().eventFilter(obj, event)

    key_listener = GlobalKeyListener()
    app.installEventFilter(key_listener)

    return main_window, key_listener  # keep ref to prevent GC


def register_screens(screen_names):
    """Import and register only the screens we need."""
    screen_map = {}

    if "evaluate" in screen_names:
        from screens import evaluate_screen
        screen_map["evaluate"] = evaluate_screen.get_ui()

    if "celebration" in screen_names:
        from screens import celebration_screen
        screen_map["celebration"] = celebration_screen.get_ui()

    if "calibration" in screen_names:
        from screens import calibration_screen
        screen_map["calibration"] = calibration_screen.get_ui()

    if "kinestatic" in screen_names:
        from screens import kinestatic
        screen_map["kinestatic"] = kinestatic.get_ui()

    if "break" in screen_names:
        from screens import break_screen
        screen_map["break"] = break_screen.get_ui()

    if "teacher_intervention" in screen_names:
        from screens import teacher_intervention
        screen_map["teacher_intervention"] = teacher_intervention.get_ui()

    if "greeting" in screen_names:
        from screens import greeting_screen
        screen_map["greeting"] = greeting_screen.get_ui()

    if "engage" in screen_names:
        from screens import engage_screen
        screen_map["engage"] = engage_screen.get_ui()

    if "explore" in screen_names:
        from screens import explore_screen
        screen_map["explore"] = explore_screen.get_ui()

    if "explain" in screen_names:
        from screens import explain_screen
        screen_map["explain"] = explain_screen.get_ui()

    if "elaborate" in screen_names:
        from screens import elaborate_screen
        screen_map["elaborate"] = elaborate_screen.get_ui()

    if "student_call" in screen_names:
        from screens import student_call_screen
        screen_map["student_call"] = student_call_screen.get_ui()

    if "session_complete" in screen_names:
        from screens import session_complete_screen
        screen_map["session_complete"] = session_complete_screen.get_ui()

    if "idle" in screen_names:
        from screens import idle_screen
        screen_map["idle"] = idle_screen.get_ui()

    if "task_intro" in screen_names:
        from screens import task_intro_screen
        screen_map["task_intro"] = task_intro_screen.get_ui()

    for name, widget in screen_map.items():
        if widget:
            navigator.register_screen(name, widget)

    return screen_map


# ════════════════════════════════════════════════
#  SCENARIO IMPLEMENTATIONS
# ════════════════════════════════════════════════

def scenario_1():
    """Smart Student — L1 correct answer."""
    print("\n🎬 SCENARIO 1: Smart Student (L1 Correct Answer)")
    print("   Press [2] for the correct answer (Right Arrow)\n")
    setup_state(level=1)
    main_window, kl = build_app()
    register_screens(["evaluate", "celebration", "greeting", "student_call", "session_complete"])
    main_window.show()
    navigator.navigate_to("evaluate")
    return app.exec()


def scenario_2():
    """Calibration Game."""
    print("\n🎬 SCENARIO 2: Calibration Game")
    print("   Press [Space] for auto-play, or [1] Open, [2] Closed, [3] Done\n")
    setup_state()
    main_window, kl = build_app()
    register_screens(["calibration"])
    main_window.show()
    navigator.navigate_to("calibration")
    return app.exec()


def scenario_3():
    """Wrong Answer → Kinesthetic."""
    print("\n🎬 SCENARIO 3: Wrong Answer → Kinesthetic")
    print("   Press [1] or [3] or [4] for a WRONG answer")
    print("   Then: [P] Pass or [F] Fail on kinesthetic screen\n")
    setup_state(level=1)
    main_window, kl = build_app()
    register_screens(["evaluate", "kinestatic", "celebration", "engage",
                       "greeting", "student_call", "session_complete"])
    main_window.show()
    navigator.navigate_to("evaluate")
    return app.exec()


def scenario_4():
    """1-Minute Motivation Nudge — shortened to 5 seconds."""
    print("\n🎬 SCENARIO 4: Motivation Nudge (5s instead of 60s)")
    print("   Wait 5 seconds — robot will speak a motivation message")
    print("   Then press [2] to answer correctly, or keep waiting\n")
    setup_state(level=1)
    main_window, kl = build_app()
    register_screens(["evaluate", "kinestatic", "celebration", "greeting",
                       "student_call", "session_complete"])

    # Monkey-patch: shorten timers
    import screens.evaluate_screen as es
    _orig_enable = es.enable_input

    def fast_enable():
        _orig_enable()
        # Override motivation timer to 5 seconds
        if es.motivation_timer:
            es.motivation_timer.setInterval(5_000)
            print("   ⚡ [DEMO] Motivation timer shortened to 5 seconds")
        # Override main timer to 30 seconds
        if es.evaluate_timer:
            es.evaluate_timer.total_seconds = 30
            es.evaluate_timer.clock_count = 6
            print("   ⚡ [DEMO] Main timer shortened to 30 seconds")

    es.enable_input = fast_enable
    main_window.show()
    navigator.navigate_to("evaluate")
    return app.exec()


def scenario_5():
    """L1 Timeout → Kinesthetic — shortened to 15 seconds."""
    print("\n🎬 SCENARIO 5: L1 Timeout → Kinesthetic (15s total)")
    print("   Just wait — nudge at 5s, timeout at 15s\n")
    setup_state(level=1)
    main_window, kl = build_app()
    register_screens(["evaluate", "kinestatic", "celebration", "greeting",
                       "student_call", "session_complete"])

    import screens.evaluate_screen as es
    _orig_enable = es.enable_input

    def fast_enable():
        _orig_enable()
        if es.motivation_timer:
            es.motivation_timer.setInterval(5_000)
        if es.evaluate_timer:
            es.evaluate_timer.total_seconds = 15
            es.evaluate_timer.clock_count = 5
            print("   ⚡ [DEMO] Timers: nudge=5s, timeout=15s")

    es.enable_input = fast_enable
    main_window.show()
    navigator.navigate_to("evaluate")
    return app.exec()


def scenario_6():
    """🐰 Rabbit Jump Break — fast timers."""
    print("\n🎬 SCENARIO 6: Rabbit Jump Break (fast timers)")
    print("   Story → Activity (10s) → Return (press ENTER)\n")
    setup_state(student="Nadun", level=2)

    # Shorten break widget timers
    from components.rabbit_break_game import RabbitBreakWidget
    RabbitBreakWidget.activity_total = 10  # default 45
    RabbitBreakWidget.return_total = 20    # default 60

    main_window, kl = build_app()
    register_screens(["break", "evaluate", "celebration", "greeting",
                       "student_call", "session_complete"])
    main_window.show()
    navigator.navigate_to("break")

    # Restore defaults on exit
    result = app.exec()
    RabbitBreakWidget.activity_total = 45
    RabbitBreakWidget.return_total = 60
    return result


def scenario_7():
    """Break Return → Retry L2."""
    print("\n🎬 SCENARIO 7: Break Return → Retry L2")
    print("   Press [ENTER] to 'come back' → goes to L2 evaluation\n")
    setup_state(student="Nadun", level=2)

    from components.rabbit_break_game import RabbitBreakWidget
    main_window, kl = build_app()
    register_screens(["break", "evaluate", "celebration", "greeting",
                       "student_call", "session_complete"])
    main_window.show()

    # Jump directly to the return phase
    from screens import break_screen
    navigator.navigate_to("break")
    # After break_screen.on_show runs, force to return phase after a short delay
    def force_return():
        if break_screen.game_widget:
            break_screen.game_widget.set_phase("return")
            break_screen.game_widget.return_remaining = 60
            break_screen.game_widget.return_running = True
            break_screen.game_widget.countdown_timer.start(1000)
            print("   ⚡ [DEMO] Jumped straight to Return phase")
    QTimer.singleShot(500, force_return)

    return app.exec()


def scenario_8():
    """Break Auto-Skip — shortened to 15 seconds."""
    print("\n🎬 SCENARIO 8: Break Auto-Skip (15s)")
    print("   DON'T press Enter — student will be auto-skipped\n")
    setup_state(student="Nadun", level=2)
    state_manager.set_student_queue(["Vidhura", "Sarith"])

    from components.rabbit_break_game import RabbitBreakWidget
    main_window, kl = build_app()
    register_screens(["break", "evaluate", "greeting", "student_call",
                       "session_complete"])
    main_window.show()

    from screens import break_screen
    navigator.navigate_to("break")

    def force_return():
        if break_screen.game_widget:
            break_screen.game_widget.return_total = 15
            break_screen.game_widget.set_phase("return")
            break_screen.game_widget.return_remaining = 15
            break_screen.game_widget.return_running = True
            break_screen.game_widget.countdown_timer.start(1000)
            break_screen.input_enabled = True
            keyboard_manager.register_handler(break_screen.handle_key_press)
            print("   ⚡ [DEMO] Return phase with 15s timeout")
    QTimer.singleShot(500, force_return)

    return app.exec()


def scenario_9():
    """L3 Auto-Skip — shortened to 15 seconds."""
    print("\n🎬 SCENARIO 9: L3 Auto-Skip (15s)")
    print("   Just wait — nudge at 5s, skip at 15s\n")
    setup_state(student="Nadun", level=3)
    state_manager.set_student_queue(["Vidhura", "Sarith"])

    main_window, kl = build_app()
    register_screens(["evaluate", "greeting", "student_call", "session_complete"])

    import screens.evaluate_screen as es
    _orig_enable = es.enable_input

    def fast_enable():
        _orig_enable()
        if es.motivation_timer:
            es.motivation_timer.setInterval(5_000)
        if es.evaluate_timer:
            es.evaluate_timer.total_seconds = 15
            es.evaluate_timer.clock_count = 5
            print("   ⚡ [DEMO] Timers: nudge=5s, skip=15s")

    es.enable_input = fast_enable
    main_window.show()
    navigator.navigate_to("evaluate")
    return app.exec()


def scenario_10():
    """Teacher Intervention — shows question + correct answer."""
    print("\n🎬 SCENARIO 10: Teacher Intervention")
    print("   Teacher sees the question, options, and correct answer highlighted")
    print("   Press [C] to continue\n")
    setup_state(student="Nadun", level=3)
    state_manager.current_path = [
        "evaluate_L1", "kinesthetic", "engage", "evaluate_L2",
        "explore", "evaluate_L3", "explain", "evaluate_L3",
        "elaborate", "evaluate_L3", "teacher_intervention"
    ]

    main_window, kl = build_app()
    register_screens(["teacher_intervention", "greeting", "student_call",
                       "session_complete"])
    main_window.show()
    navigator.navigate_to("teacher_intervention")
    return app.exec()


def scenario_11():
    """Full Cascade with fast timers."""
    print("\n🎬 SCENARIO 11: Full Cascade (fast timers)")
    print("   Press WRONG answers to progress through the cascade")
    print("   Timers shortened to 10s")
    print("   Press [ENTER] on 5E screens to advance\n")
    setup_state(student="Nadun", level=1)
    state_manager.set_student_queue(["Vidhura"])

    main_window, kl = build_app()
    register_screens(["evaluate", "kinestatic", "engage", "explore",
                       "explain", "elaborate", "teacher_intervention",
                       "celebration", "break", "greeting", "student_call",
                       "session_complete"])
    main_window.show()
    navigator.navigate_to("evaluate")
    return app.exec()


def scenario_12():
    """RL Smart Start — pre-seed DB."""
    print("\n🎬 SCENARIO 12: RL Smart Start")
    print("   Pre-seeding DB so Nadun starts at L2 (engage method)...")

    import core.database as database
    database.init_db()
    session_id = database.start_session("demo_teacher")
    database.log_student_metric(session_id, "Nadun", "evaluate_L2", "engage")
    print("   ✅ DB seeded: Nadun → method=engage, passed=evaluate_L2")
    print("   Robot should start Nadun at L2 (skipping L1)")
    print("\n   Press [2] for correct answer\n")

    setup_state(student="Nadun", level=1)

    # Let flow_controller compute the start point
    from core.flow_controller import flow_controller
    flow_controller.reset_cascade()
    start_screen = flow_controller.setup_dynamic_start("Nadun")
    print(f"   🧠 RL computed start screen: {start_screen}")

    main_window, kl = build_app()
    register_screens(["evaluate", "celebration", "kinestatic", "engage",
                       "explore", "explain", "elaborate",
                       "teacher_intervention", "greeting", "student_call",
                       "session_complete"])
    main_window.show()
    navigator.navigate_to(start_screen)
    return app.exec()


def print_help():
    """Print all scenarios."""
    print("""
🎬 Akshi Robot — Client Demo Launcher
=======================================

Usage: python demo.py <number>

  1  — Smart Student (L1 correct → celebration)
  2  — Calibration Game (3-act mini-game)
  3  — Wrong Answer → Kinesthetic
  4  — Motivation Nudge (5s timer)
  5  — L1 Timeout → Kinesthetic (15s timer)
  6  — 🐰 Rabbit Jump Break (10s activity)
  7  — Break Return → Retry L2
  8  — Break Auto-Skip (15s timer)
  9  — L3 Auto-Skip (15s timer)
 10  — Teacher Intervention (question revealed)
 11  — Full Cascade (manual, fast timers)
 12  — RL Smart Start (pre-seeded DB)
  0  — Show this help

Example:
  python demo.py 6     # Rabbit Jump Break demo
  python demo.py 10    # Teacher Intervention demo
""")


# ════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════

SCENARIOS = {
    0: print_help,
    1: scenario_1,
    2: scenario_2,
    3: scenario_3,
    4: scenario_4,
    5: scenario_5,
    6: scenario_6,
    7: scenario_7,
    8: scenario_8,
    9: scenario_9,
    10: scenario_10,
    11: scenario_11,
    12: scenario_12,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    try:
        num = int(sys.argv[1])
    except ValueError:
        print(f"❌ Invalid scenario: {sys.argv[1]}")
        print_help()
        sys.exit(1)

    if num not in SCENARIOS:
        print(f"❌ Unknown scenario: {num}")
        print_help()
        sys.exit(1)

    if num == 0:
        print_help()
    else:
        sys.exit(SCENARIOS[num]())
