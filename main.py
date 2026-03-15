import sys
import datetime

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

import firebase
import evaluation
import elaborate
import engage
import explain
import explore
import kinestatic


app = QApplication(sys.argv)
loader = QUiLoader()


def load_ui(path):

    file = QFile(path)

    if not file.open(QFile.ReadOnly):
        print("Cannot open UI file:", path)
        sys.exit()

    ui = loader.load(file)
    file.close()

    return ui


main_window = QMainWindow()
stack = QStackedWidget()


# Load teacher UI
teacher_ui = load_ui("mainUI.ui")

dropdown = teacher_ui.teacher_dropdown
submit_btn = teacher_ui.submit_btn


# Load learning screens
evaluation_screen = evaluation.get_ui()



# Add screens to stack
stack.addWidget(teacher_ui)        # index 0
stack.addWidget(evaluation_screen) # index 1



# Ensure teacher screen appears first
stack.setCurrentIndex(0)

main_window.setCentralWidget(stack)


# Load teachers from Firebase
teachers = firebase.get_teachers()

for t in teachers:
    dropdown.addItem(t)


def check_teacher():

    selected = dropdown.currentText()

    data = firebase.get_teacher_data(selected)

    if not data:
        print("Teacher not found")
        return

    today = datetime.date.today().strftime("%Y-%m-%d")

    attendance = data.get("attendance", {})

    if today in attendance:

        lesson_id = data.get("current_lesson")

        print("Starting lesson:", lesson_id)

        stack.setCurrentIndex(1)

        evaluation.start_lesson(lesson_id)

    else:

        print("Set attendees and lesson to move from the teacher's web dashboard")


submit_btn.clicked.connect(check_teacher)


main_window.show()

sys.exit(app.exec())