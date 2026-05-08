#!/usr/bin/env python3
"""Generate the Ginglu Robot Demo Guide PDF."""

from fpdf import FPDF
import os

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Ginglu_Robot_Demo_Guide.pdf"
)


class DemoGuidePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Ginglu Robot - Demo Guide", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(66, 133, 244)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title, r=33, g=37, b=41):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(r, g, b)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_title(self, title, r=66, g=133, b=244):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(r, g, b)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def code_block(self, text):
        self.set_font("Courier", "", 10)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text, fill=True)
        self.ln(2)

    def add_table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        # Header
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(66, 133, 244)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        for row_idx, row in enumerate(rows):
            fill = row_idx % 2 == 0
            if fill:
                self.set_fill_color(245, 248, 255)
            else:
                self.set_fill_color(255, 255, 255)
            max_h = 7
            for i, cell in enumerate(row):
                self.cell(col_widths[i], max_h, str(cell), border=1, fill=True, align="C" if i == 0 else "L")
            self.ln()
        self.ln(3)

    def scenario_block(self, num, title, description, command, keys, timer_info="Normal"):
        # Check if we need a new page
        if self.get_y() > 240:
            self.add_page()

        # Scenario header
        self.set_font("Helvetica", "B", 11)
        colors = {
            1: (76, 175, 80), 2: (76, 175, 80), 3: (255, 193, 7),
            4: (255, 193, 7), 5: (255, 193, 7), 6: (33, 150, 243),
            7: (33, 150, 243), 8: (33, 150, 243), 9: (244, 67, 54),
            10: (244, 67, 54), 11: (156, 39, 176), 12: (156, 39, 176)
        }
        r, g, b = colors.get(num, (66, 66, 66))
        self.set_text_color(r, g, b)
        self.cell(0, 7, f"Scenario {num}: {title}", new_x="LMARGIN", new_y="NEXT")

        # Description
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        self.multi_cell(0, 5, description)
        self.ln(1)

        # Command
        self.set_font("Courier", "B", 10)
        self.set_fill_color(35, 35, 40)
        self.set_text_color(130, 255, 130)
        self.cell(0, 7, f"  $ {command}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

        # Keys + Timer in a mini table
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.cell(30, 5, "Keys:", new_x="RIGHT")
        self.set_font("Courier", "", 9)
        self.cell(80, 5, keys, new_x="RIGHT")
        self.set_font("Helvetica", "", 9)
        self.cell(20, 5, "Timer:", new_x="RIGHT")
        self.set_font("Courier", "", 9)
        self.cell(0, 5, timer_info, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)


def generate():
    pdf = DemoGuidePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ═══════════════════ PAGE 1: COVER ═══════════════════
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 20, "Ginglu Robot", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 12, "Client Demo Guide", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    pdf.set_draw_color(66, 133, 244)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(12)

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "12 Interactive Demo Scenarios", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "with Shortened Timers for Quick Presentations", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(30)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "Adaptive Robot-Assisted Education for Preschoolers", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Powered by 5E Learning Model + Reinforcement Learning", align="C", new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════ PAGE 2: QUICK START ═══════════════════
    pdf.add_page()
    pdf.section_title("Quick Start")
    pdf.body_text(
        "Each scenario can be launched with a single command. "
        "Timer-heavy scenarios (motivation nudges, timeouts) use shortened timers "
        "so you can demo any flow in under 30 seconds."
    )

    pdf.sub_title("Launch any scenario:")
    pdf.code_block("python demo.py <scenario_number>")

    pdf.sub_title("Reset student data (SQLite only, Firebase untouched):")
    pdf.code_block("python reset_sqlite.py")

    pdf.sub_title("Show all scenarios:")
    pdf.code_block("python demo.py 0")

    # ═══════════════════ PAGE 3: OVERVIEW TABLE ═══════════════════
    pdf.add_page()
    pdf.section_title("All Scenarios at a Glance")

    pdf.add_table(
        headers=["#", "Scenario", "Command", "Timer", "Key"],
        col_widths=[10, 60, 50, 30, 40],
        rows=[
            ["1",  "Smart Student",           "python demo.py 1",  "Normal", "Press 2"],
            ["2",  "Calibration Game",         "python demo.py 2",  "Normal", "Space"],
            ["3",  "Wrong Answer",             "python demo.py 3",  "Normal", "Press 1/3/4"],
            ["4",  "Motivation Nudge",         "python demo.py 4",  "5s",     "Wait & watch"],
            ["5",  "L1 Timeout",               "python demo.py 5",  "15s",    "Just wait"],
            ["6",  "Rabbit Jump Break",        "python demo.py 6",  "10s",    "Watch + Enter"],
            ["7",  "Break Return",             "python demo.py 7",  "Normal", "Press Enter"],
            ["8",  "Break Auto-Skip",          "python demo.py 8",  "15s",    "Don't press"],
            ["9",  "L3 Auto-Skip",             "python demo.py 9",  "15s",    "Just wait"],
            ["10", "Teacher Intervention",     "python demo.py 10", "Normal", "Press C"],
            ["11", "Full Cascade",             "python demo.py 11", "Fast",   "Wrong answers"],
            ["12", "RL Smart Start",           "python demo.py 12", "Normal", "Press 2"],
        ]
    )

    # ═══════════════════ PAGE 4-5: DETAILED SCENARIOS ═══════════════════
    pdf.add_page()
    pdf.section_title("Detailed Scenario Descriptions")

    pdf.scenario_block(
        1, "Smart Student (Happy Path)",
        "Student sees the Level 1 evaluation with 4 answer options. They press the correct answer (key 2 = Right Arrow) and the robot celebrates with voice and animation.",
        "python demo.py 1", "Press [2] for correct", "Normal"
    )

    pdf.scenario_block(
        2, "Calibration Game",
        "The beautiful 'Magical Eyes' calibration mini-game. 3 acts: Owl (eyes open), Sleeping Bunny (eyes closed), Celebration (calibration complete). Press Space for auto-play.",
        "python demo.py 2", "[Space] auto / [1][2][3] manual", "Normal"
    )

    pdf.scenario_block(
        3, "Wrong Answer -> Kinesthetic",
        "Student gives a wrong answer at L1. Robot gives encouragement speech, then escalates to the Kinesthetic activity screen where the teacher judges Pass [P] or Fail [F].",
        "python demo.py 3", "[1]/[3]/[4] wrong, then [P]/[F]", "Normal"
    )

    pdf.scenario_block(
        4, "1-Minute Motivation Nudge",
        "Student doesn't answer. After 5 seconds (shortened from 60s), the robot speaks a motivational message encouraging them to try. Timer continues running.",
        "python demo.py 4", "Wait 5s, then [2] to answer", "5s (was 60s)"
    )

    pdf.scenario_block(
        5, "L1 Timeout -> Kinesthetic",
        "Student remains unresponsive. Motivation nudge at 5s, then full timeout at 15s (shortened from 180s). Robot automatically transitions to the Kinesthetic test.",
        "python demo.py 5", "Just wait and watch", "15s (was 180s)"
    )

    pdf.scenario_block(
        6, "Rabbit Jump Break (L2)",
        "The full gamified bunny hop break! 3 acts: Story (robot tells child to hop), Activity (10s countdown with bunny hopping along a path), Return (press Enter to come back).",
        "python demo.py 6", "Watch, then [Enter]", "10s (was 45s)"
    )

    pdf.scenario_block(
        7, "Break Return -> Retry L2",
        "Jumps directly to the Return phase of the break screen. Student presses Enter to 'come back' and the system retries the Level 2 evaluation.",
        "python demo.py 7", "Press [Enter]", "Normal"
    )

    pdf.scenario_block(
        8, "Break Auto-Skip",
        "Student doesn't return after the break. The system counts down 15s (shortened from 60s), gives a verbal warning at 15s remaining, then automatically skips to the next student.",
        "python demo.py 8", "Don't press anything", "15s (was 60s)"
    )

    pdf.scenario_block(
        9, "L3 Auto-Skip",
        "Level 3 student is completely unresponsive. Gentle motivation nudge at 5s, then at 15s (shortened from 180s) the robot says goodbye and skips to the next student.",
        "python demo.py 9", "Just wait and watch", "15s (was 180s)"
    )

    pdf.scenario_block(
        10, "Teacher Intervention",
        "The final escalation. Teacher sees a gamified screen showing: the exact question, all answer options with images, the correct answer highlighted with a star, and the student's learning path.",
        "python demo.py 10", "Press [C] to continue", "Normal"
    )

    pdf.scenario_block(
        11, "Full Cascade (Interactive)",
        "Walk through the entire escalation ladder: L1 -> Kinesthetic -> Engage -> L2 -> Explore -> L3 -> Explain -> L3 -> Elaborate -> L3 -> Teacher. Press wrong answers to progress.",
        "python demo.py 11", "Wrong keys + [Enter]", "Fast"
    )

    pdf.scenario_block(
        12, "RL Smart Start",
        "Pre-seeds the database with student history, then shows how the robot intelligently skips to the optimal starting level. Demonstrates the Reinforcement Learning adaptation.",
        "python demo.py 12", "Press [2] for correct", "Normal"
    )

    # ═══════════════════ PAGE: RECOMMENDED DEMO ORDER ═══════════════════
    pdf.add_page()
    pdf.section_title("Recommended Demo Order")
    pdf.body_text(
        "For the best client impression, follow this order. "
        "Total presentation time: approximately 5 minutes."
    )

    pdf.add_table(
        headers=["Order", "Scenario", "Why Show This", "Time"],
        col_widths=[15, 55, 90, 30],
        rows=[
            ["1", "Calibration Game",     "Visual wow factor - stunning animated scenes",       "~30s"],
            ["2", "Smart Student",         "Happy path - shows the basic evaluation flow",       "~15s"],
            ["3", "Wrong Answer",          "Shows robot encouragement and escalation",           "~20s"],
            ["4", "Motivation Nudge",      "Shows the robot cares about the child",              "~15s"],
            ["5", "Rabbit Jump Break",     "Star feature - gamified physical activity break",    "~30s"],
            ["6", "Teacher Intervention",  "Shows question + correct answer for teacher",        "~15s"],
            ["7", "RL Smart Start",        "Shows intelligent adaptation to student history",    "~20s"],
        ]
    )

    # ═══════════════════ PAGE: SYSTEM ARCHITECTURE ═══════════════════
    pdf.add_page()
    pdf.section_title("Evaluation Timeout Behavior")
    pdf.body_text(
        "Each evaluation level has different timeout behavior "
        "to handle unresponsive students appropriately:"
    )

    pdf.add_table(
        headers=["Level", "At 1 Minute", "At 3 Minutes"],
        col_widths=[30, 80, 80],
        rows=[
            ["Level 1", "Gentle motivation nudge",    "Escalate to Kinesthetic test"],
            ["Level 2", "Strong motivation nudge",    "Rabbit Jump Break -> Retry L2"],
            ["Level 3", "Supportive gentle nudge",    "Auto-skip to next student"],
        ]
    )

    pdf.section_title("Learning Escalation Cascade")
    pdf.body_text(
        "When a student answers incorrectly, the system follows this deterministic cascade. "
        "Each step provides more scaffolding before re-evaluating:"
    )

    cascade = [
        ["1", "Evaluate L1",             "4 options, full question"],
        ["2", "Kinesthetic Activity",     "Physical learning (teacher judged)"],
        ["3", "Engage",                   "Interactive video activity"],
        ["4", "Evaluate L2",             "2 options, simplified"],
        ["5", "Explore",                  "Immersive storytelling"],
        ["6", "Evaluate L3",             "2 options, personalized"],
        ["7", "Explain",                  "Direct concept explanation"],
        ["8", "Evaluate L3",             "Re-evaluation"],
        ["9", "Elaborate",                "Guided practice with hints"],
        ["10", "Evaluate L3",            "Final re-evaluation"],
        ["11", "Teacher Intervention",    "Human teacher takes over"],
    ]
    pdf.add_table(
        headers=["Step", "Stage", "Description"],
        col_widths=[15, 55, 120],
        rows=cascade
    )

    # ═══════════════════ PAGE: KEY MAPPINGS ═══════════════════
    pdf.add_page()
    pdf.section_title("Keyboard Controls Reference")

    pdf.add_table(
        headers=["Key", "Action", "Used In"],
        col_widths=[30, 60, 100],
        rows=[
            ["1, 2, 3, 4", "Select answer option",     "Evaluation screens"],
            ["Enter",       "Confirm / Continue",        "5E screens, Break return"],
            ["C",           "Teacher Continue",          "Teacher Intervention"],
            ["P",           "Teacher Pass",              "Kinesthetic screen"],
            ["F",           "Teacher Fail",              "Kinesthetic screen"],
            ["B",           "Request Break",             "L2+ Evaluation"],
            ["S",           "Skip question",             "L3 Evaluation"],
            ["W",           "Wake robot",                "Idle screen"],
            ["Space",       "Auto-play",                 "Calibration game"],
        ]
    )

    pdf.section_title("Utility Commands")

    pdf.sub_title("Reset Database (SQLite only)")
    pdf.code_block("python reset_sqlite.py")
    pdf.body_text("Clears all student metrics and session history from the local database. Firebase cloud data is NOT affected.")

    pdf.sub_title("Run Full Application")
    pdf.code_block("python main.py")
    pdf.body_text("Launches the complete Ginglu Robot interface with all screens, backend, and real timers.")

    pdf.sub_title("Run Individual Demo")
    pdf.code_block("python demo.py <1-12>")
    pdf.body_text("Launches a specific scenario with shortened timers for quick presentations.")

    # ═══════════════════ SAVE ═══════════════════
    pdf.output(OUTPUT_PATH)
    print(f"PDF saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
