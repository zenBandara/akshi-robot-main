import QtQuick 2.15

Rectangle {
    width: 200
    height: 200
    color: "transparent"

    // Load native Qt.labs renderer mapping to the local Lottie string
    Component.onCompleted: {
        var lottie = Qt.createQmlObject('import Qt.labs.lottieqt 1.0; LottieAnimation { source: "assets/lottiefiles/adle.json"; loops: LottieAnimation.Infinite; autoPlay: true; anchors.fill: parent; }', parent, "dynamicLottie");
    }
}
