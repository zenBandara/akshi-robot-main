
import QtQuick 2.15
import Qt.labs.lottieqt 1.0

Rectangle {
    width: 450
    height: 450
    color: "transparent"

    LottieAnimation {
        anchors.fill: parent
        source: "file:///Users/dinujaya_s/Documents/Development Tools/Python/akshi-robot-main/assets/lottiefiles/adle.json"
        loops: LottieAnimation.Infinite
        autoPlay: true
    }
}
