from core.voice_manager import VoiceManager


class RobotTask:

    def __init__(self):
        self.voice = VoiceManager()

    def start(self):

        text = "You are doing great! Keep up the good work. Wow!!!"
        audio_name = "encourage_message"
        rate = "-15%"

        self.voice.speak(text, audio_name, rate)


if __name__ == "__main__":
    task = RobotTask()
    task.start()