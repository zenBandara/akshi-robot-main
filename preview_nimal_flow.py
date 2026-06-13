import sys
import os
import json

from PySide6.QtWidgets import QApplication, QStackedWidget, QMainWindow
from PySide6.QtCore import QTimer

def main():
    app = QApplication(sys.argv)

    # Boot components
    from core.state_manager import state_manager
    from core.keyboard_manager import keyboard_manager
    from core.navigator import navigator
    from screens import (
        student_call_screen, evaluate_screen, elaborate_screen, 
        engage_screen, explain_screen, explore_screen,
        teacher_intervention, kinestatic, task_intro_screen,
        calibration_screen, break_screen, water_break_screen
    )

    with open('Tasks/task_jsons/t_1.json', 'r') as f:
        task_data = json.load(f)

    # Initialize State for Nimal
    state_manager.set_current_task(task_data)
    state_manager.set_student_queue([{"first_name": "Nimal", "id": "1"}])
    state_manager.set_current_student("Nimal")
    
    class MockWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.stack = QStackedWidget()
            self.setCentralWidget(self.stack)

    main_window = MockWindow()
    main_window.resize(1280, 720)
    main_window.show()
    navigator.set_stack(main_window.stack)

    screens_dict = {
        "student_call": student_call_screen.get_ui(),
        "task_intro": task_intro_screen.get_ui(),
        "calibration": calibration_screen.get_ui(),
        "evaluate": evaluate_screen.get_ui(),
        "elaborate": elaborate_screen.get_ui(),
        "engage": engage_screen.get_ui(),
        "explain": explain_screen.get_ui(),
        "explore": explore_screen.get_ui(),
        "teacher_intervention": teacher_intervention.get_ui(),
        "kinestatic": kinestatic.get_ui(),
        "break": break_screen.get_ui(),
        "water_break": water_break_screen.get_ui(),
    }

    for name, widget in screens_dict.items():
        if widget:
            navigator.register_screen(name, widget)

    # Start the flow
    navigator.navigate_to("calibration")

    # MOCK CALIBRATION BACKEND
    state_file = os.path.join("ginglu-the-robot", "calibration_state.json")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    tick = {"n": 0}
    def write_calib_status():
        if state_manager.get_current_screen() == "calibration":
            if getattr(screens_dict["calibration"].game, "_clock_enabled", False):
                tick["n"] += 2
                status = "DONE" if tick["n"] > 20 else f"Keep eyes OPEN ({tick['n']}/20)"
                try:
                    with open(state_file, "w", encoding="utf-8") as f:
                        json.dump({"calibration_status": status}, f)
                except Exception:
                    pass

    calib_timer = QTimer()
    calib_timer.timeout.connect(write_calib_status)
    calib_timer.start(100)

    # BOT LOGIC
    def auto_bot():
        screen = state_manager.get_current_screen()
        if screen == "evaluate":
            import screens.evaluate_screen as eval_scr
            if eval_scr.input_enabled and eval_scr.awaiting_yes_no:
                print(f"\n[BOT] Pressing NO in Evaluate! (Student: {state_manager.get_current_student()})")
                keyboard_manager._on_voice_command("NO")
        elif screen in ["kinesthetic", "kinestatic"]:
            import screens.kinestatic as kin_scr
            if kin_scr.input_enabled:
                print("\n[BOT] Pressing NO in Kinesthetic!")
                keyboard_manager._on_voice_command("NO")
        elif screen in ["engage", "explain", "explore", "task_intro", "student_call"]:
            mod_map = {
                "engage": engage_screen,
                "explain": explain_screen,
                "explore": explore_screen,
                "task_intro": task_intro_screen,
                "student_call": student_call_screen
            }
            mod = mod_map[screen]
            if mod.input_enabled:
                print(f"\n[BOT] Pressing YES in {screen.upper()} to advance!")
                keyboard_manager._on_voice_command("YES")
        elif screen == "elaborate":
            import screens.elaborate_screen as elab_scr
            if elab_scr.input_enabled:
                print("\n[BOT] Pressing YES in Elaborate to advance!")
                keyboard_manager._on_voice_command("YES")
        elif screen == "teacher_intervention":
            print("\n=========================================")
            print("[BOT] ✨ TEACHER INTERVENTION REACHED! ✨")
            print("[BOT] Flow successful. Terminating program.")
            print("=========================================\n")
            app.quit()

    bot_timer = QTimer()
    bot_timer.timeout.connect(auto_bot)
    bot_timer.start(1000)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
