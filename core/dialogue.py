import random

class DialoguePool:
    """The central algorithmic intelligence processing dynamically scalable semantic praise matrices."""
    
    CORRECT = [
        "Wow, {name}! You got it right! You're a superstar! 🌟",
        "Amazing job, {name}! That is totally correct! 🎉",
        "Fantastic work, {name}! You are so smart! 💡",
        "You nailed it, {name}! You are a genius! ✨",
        "Brilliant, {name}! That's exactly right! 🚀",
        "Way to go, {name}! You figured it out! 🏆"
    ]
    
    INCORRECT_L1 = [
        "Oops, {name}! That's not quite right. Let's look closer!",
        "Not exactly, {name}. But we can figure it out together!",
        "Hmm, let's try a different way, {name}!"
    ]
    
    INCORRECT_L2 = [
        "Still not quite right, {name}. Don't worry, let's keep trying!",
        "That's okay, {name}! Learning takes practice.",
        "Almost there, {name}! Let's look at it another way."
    ]
    
    INCORRECT_L3 = [
        "It's tricky, {name}! Let's stand up and try something else!",
        "I know this is hard, {name}. Let's try a fun activity instead!",
        "Don't give up, {name}! Let's move around and figure this out!"
    ]
    
    TIMEOUT = [
        "Take your time, {name}. I'm right here with you.",
        "Need a little more time, {name}? That's totally okay.",
        "No rush, {name}. Thinking takes time!"
    ]

    MOTIVATION_NUDGE = [
        "Hey {name}, you're doing great! Take a nice look at the picture and say yes or no!",
        "Don't worry {name}! There's no wrong answer here. Just say yes or no!",
        "I believe in you, {name}! Look at the picture carefully. You can do this!",
        "{name}, remember, you're a superstar! Just say yes if you think it's correct, or no if it's not!",
        "Hey {name}! It's okay to take your time. Look at the picture one more time and say yes or no!",
        "You've got this, {name}! Do you think this picture is the answer? Go ahead and say yes or no!"
    ]

    MOTIVATION_NUDGE_L2 = [
        "Come on {name}, you can do it! Look at the picture really carefully. Do you think it's right? Just say yes or no!",
        "Hey {name}! I know you know this! Take a deep breath and say yes if it looks correct. You're so close!",
        "{name}, you're a champion! Don't be shy, just say yes or no! I believe in you!",
        "I'm rooting for you, {name}! Just look one more time and say yes or no. You've totally got this!",
        "{name}, you're one of the smartest kids I know! Just say yes if the picture looks right. I believe in you!"
    ]

    MOTIVATION_NUDGE_L3 = [
        "{name}, take a deep breath. You are doing amazing! Just say yes or no when you are ready.",
        "It's okay to feel stuck, {name}. Just give it your best guess by saying yes or no! I'm proud of you no matter what.",
        "Take all the time you need, {name}. Look at the choice on the screen and say yes or no.",
        "You've worked so hard today, {name}! Just one more try. You're doing wonderful! Just say yes or no!"
    ]

    SKIP_L3 = [
        "It looks like you're feeling really tired, {name}. That's totally okay! We'll stop here for now. You did a great job today!",
        "Let's take a rest, {name}. You've done enough hard work today! I'm very proud of you. We'll let the next friend have a turn.",
        "I think we've done enough thinking for today, {name}! You were amazing. Let's move on to the next student!"
    ]

    BREAK_STORY = [
        "Hey {name}! I can see you're thinking really hard! Let's take a super fun break! Can you stand up and hop like a bunny? Hop around and come back to me! Ready? Go!",
        "Oh {name}, you look like you could use some energy! Let's play a fun game! Stand up, hop like a little bunny rabbit, go for a round, and hop back! Ready? Let's go!",
        "Time for a bunny break, {name}! Stand up, stretch your legs, and hop hop hop like a cute little rabbit! Go around and come back when you hear me call! Ready? Hop!"
    ]

    BREAK_RETURN = [
        "Wow {name}, that was amazing hopping! You must feel so energized now! Come sit down and say 'Okay' when you're ready to try again!",
        "Great job hopping, {name}! You're such a fast bunny! Now come back to your seat and say 'Okay'. Let's try the question again!",
        "Awesome, {name}! What fantastic hopping! Come back, sit down, and say 'Okay' when you're ready. I know you can do it this time!"
    ]

    BREAK_HURRY = [
        "Come on {name}, I'm waiting for you! Hop back to your seat and say 'Okay'! We've got more fun things to do!",
        "{name}, the break is almost over! Come back quick and say 'Okay'! I miss you!",
        "Hey {name}, hurry back! Say 'Okay' when you're in your seat! Let's keep going!"
    ]

    WAITING_THINKING = [
        "Hmm, this is an interesting one...",
        "I wonder what the answer could be...",
        "Let's think about this together...",
        "Take a deep breath and look closely."
    ]

    @classmethod
    def _get_pool(cls, category):
        """Internal helper to look up the phrase pool for a given category."""
        pools = {
            "correct": cls.CORRECT,
            "incorrect_L1": cls.INCORRECT_L1,
            "incorrect_L2": cls.INCORRECT_L2,
            "incorrect_L3": cls.INCORRECT_L3,
            "timeout": cls.TIMEOUT,
            "motivation_nudge": cls.MOTIVATION_NUDGE,
            "motivation_nudge_l2": cls.MOTIVATION_NUDGE_L2,
            "motivation_nudge_l3": cls.MOTIVATION_NUDGE_L3,
            "skip_l3": cls.SKIP_L3,
            "break_story": cls.BREAK_STORY,
            "break_return": cls.BREAK_RETURN,
            "break_hurry": cls.BREAK_HURRY,
            "thinking": cls.WAITING_THINKING
        }
        return pools.get(category, ["Great job, {name}!"])

    @classmethod
    def get_phrase(cls, category, student_name="Superstar"):
        """Extract a mathematically pseudo-random natural language processing string securely formatting dynamic child names."""
        target_pool = cls._get_pool(category)
        return random.choice(target_pool).format(name=student_name)

    @classmethod
    def get_template(cls, category, student_name="Superstar"):
        """Returns (template_string, student_name) tuple for use with speak_with_name().
        
        The template contains the raw {name} placeholder instead of the formatted name,
        enabling the VoiceManager to split the audio into reusable segments.
        
        Args:
            category: The dialogue category (e.g. "correct", "break_story")
            student_name: The student's name
            
        Returns:
            Tuple of (template_string_with_{name}_placeholder, student_name)
        """
        target_pool = cls._get_pool(category)
        template = random.choice(target_pool)
        return template, student_name
