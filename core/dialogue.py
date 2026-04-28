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
        "Hey {name}, you're doing great! Take a nice look at the pictures and pick the one you think is right!",
        "Don't worry {name}! There's no wrong answer here. Just pick the one that feels right to you!",
        "I believe in you, {name}! Look at each picture carefully. You can do this!",
        "{name}, remember, you're a superstar! Just press the number of the picture you think is correct!",
        "Hey {name}! It's okay to take your time. Look at the pictures one more time and give it a try!",
        "You've got this, {name}! Which picture do you think is the answer? Go ahead and press the number!"
    ]

    MOTIVATION_NUDGE_L2 = [
        "Come on {name}, you can do it! Look at the two pictures really carefully. Which one feels right? Just press 1 or 2!",
        "Hey {name}! I know you know this! Take a deep breath and pick the one that looks correct. You're so close!",
        "{name}, you're a champion! Don't be shy, just pick one! There's only two choices, you've got a great chance!",
        "I'm rooting for you, {name}! Just look one more time and press the number. You've totally got this!",
        "{name}, you're one of the smartest kids I know! Just pick the picture that looks right. I believe in you!"
    ]

    MOTIVATION_NUDGE_L3 = [
        "{name}, take a deep breath. You are doing amazing! Pick the answer that feels right to you.",
        "It's okay to feel stuck, {name}. Just give it your best guess! I'm proud of you no matter what.",
        "Take all the time you need, {name}. Look at the choices and pick your favorite one.",
        "You've worked so hard today, {name}! Just one more try. You're doing wonderful!"
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
        "Wow {name}, that was amazing hopping! You must feel so energized now! Come sit down and press the green Enter button when you're ready to try again!",
        "Great job hopping, {name}! You're such a fast bunny! Now come back to your seat and press Enter. Let's try the question again!",
        "Awesome, {name}! What fantastic hopping! Come back, sit down, and press Enter when you're ready. I know you can do it this time!"
    ]

    BREAK_HURRY = [
        "Come on {name}, I'm waiting for you! Hop back to your seat and press Enter! We've got more fun things to do!",
        "{name}, the break is almost over! Come back quick and press Enter! I miss you!",
        "Hey {name}, hurry back! Press Enter when you're in your seat! Let's keep going!"
    ]

    WAITING_THINKING = [
        "Hmm, this is an interesting one...",
        "I wonder what the answer could be...",
        "Let's think about this together...",
        "Take a deep breath and look closely."
    ]

    @classmethod
    def get_phrase(cls, category, student_name="Superstar"):
        """Extract a mathematically pseudo-random natural language processing string securely formatting dynamic child names."""
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
        
        target_pool = pools.get(category, ["Great job, {name}!"])
        return random.choice(target_pool).format(name=student_name)
