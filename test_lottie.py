import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, QTimer

app = QApplication(sys.argv)
view = QQuickWidget()
view.setSource(QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), "test_lottie.qml")))

errors = view.errors()
if errors:
    for e in errors:
        print(e.toString())
else:
    print("SUCCESS_LOTTIE_QML")

QTimer.singleShot(1000, app.quit)
app.exec()
