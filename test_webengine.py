import sys
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --disable-gpu-sandbox"

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QTimer

app = QApplication(sys.argv)
win = QMainWindow()
win.setStyleSheet("background-color: white;")
central = QWidget()
layout = QVBoxLayout(central)

web_view = QWebEngineView()
web_view.setStyleSheet("background: transparent;")
web_view.page().setBackgroundColor(Qt.transparent)

html_content = """
<!DOCTYPE html>
<html>
<body style="background-color: red;">
    <h1>Testing WebEngine</h1>
</body>
</html>
"""
web_view.setHtml(html_content)

layout.addWidget(web_view)
win.setCentralWidget(central)
win.show()

print("WebEngine Booted Successfully!")
QTimer.singleShot(2000, app.quit)
app.exec()
