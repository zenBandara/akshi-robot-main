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
            "thinking": cls.WAITING_THINKING
        }
        
        target_pool = pools.get(category, ["Great job, {name}!"])
        return random.choice(target_pool).format(name=student_name)
