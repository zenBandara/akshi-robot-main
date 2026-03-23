import sys
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --disable-gpu-sandbox"

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QTimer

app = QApplication(sys.argv)
win = QMainWindow()
stack = QStackedWidget()

win.setCentralWidget(stack)

page1 = QWidget()
layout = QVBoxLayout(page1)

web_view = QWebEngineView(page1)
web_view.page().setBackgroundColor(Qt.transparent)
web_view.setHtml("<html><body style='background-color: transparent;'>Test</body></html>")

layout.addWidget(web_view)
stack.addWidget(page1)
stack.setCurrentWidget(page1)

win.show()
print("Successfully launched!")
QTimer.singleShot(2000, app.quit)
app.exec()
