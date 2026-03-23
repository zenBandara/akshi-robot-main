import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, Qt, QTimer

app = QApplication(sys.argv)
win = QMainWindow()
win.setStyleSheet("background-color: white;")
central = QWidget()
layout = QVBoxLayout(central)

project_root = os.path.dirname(__file__)
qml_path = os.path.join(project_root, "assets", "lottiefiles", "idle_lottie.qml")

lottie_view = QQuickWidget()
lottie_view.setAttribute(Qt.WA_AlwaysStackOnTop)
lottie_view.setAttribute(Qt.WA_TranslucentBackground)
lottie_view.setClearColor(Qt.transparent)
lottie_view.setResizeMode(QQuickWidget.SizeRootObjectToView)
lottie_view.setSource(QUrl.fromLocalFile(qml_path))

errors = lottie_view.errors()
if errors:
    for e in errors:
        print("QML ERROR:", e.toString())
else:
    # Check if the animation element was created successfully and its status
    root = lottie_view.rootObject()
    if root:
        print("Root Object created successfully:", root)
    else:
        print("Failed to create Root Object!")

layout.addWidget(lottie_view)
win.setCentralWidget(central)
win.show()

QTimer.singleShot(2000, app.quit)
app.exec()
