import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl, Qt, QTimer

app = QApplication(sys.argv)
win = QMainWindow()
win.resize(800, 600)
win.setStyleSheet("background-color: white;")

central = QWidget()
layout = QVBoxLayout(central)

# Put it in a container
container = QWidget()
container_layout = QVBoxLayout(container)
container_layout.setContentsMargins(0, 0, 0, 0)

video_widget = QVideoWidget()
# Fix black bars:
video_widget.setStyleSheet("background-color: white;")

# Alternatively try palette if stylesheet fails
# palette = video_widget.palette()
# palette.setColor(video_widget.backgroundRole(), Qt.white)
# video_widget.setPalette(palette)
# video_widget.setAutoFillBackground(True)

container_layout.addWidget(video_widget)
layout.addWidget(container)
win.setCentralWidget(central)

player = QMediaPlayer()
audio = QAudioOutput()
audio.setVolume(0)
player.setAudioOutput(audio)
player.setVideoOutput(video_widget)

project_root = os.path.dirname(__file__)
video_path = os.path.join(project_root, "assets", "video", "idle.mp4")
player.setSource(QUrl.fromLocalFile(video_path))
player.play()

win.show()

# Test screenshot to verify if bars are white
def check():
    pixmap = win.grab()
    pixmap.save("test_screenshot.png")
    app.quit()

QTimer.singleShot(2000, check)
app.exec()
