import random
from questions import QUESTION_BANK

LEVELS = ["Beginner", "Intermediate", "Advanced"]
SUBJECTS = ["Science", "Technology", "Engineering", "Arts", "Math"]

class STEAMQuizAgent:
    def question_set(self, subject, difficulty, count=5, seed=None):
        pool = list(QUESTION_BANK[subject][difficulty])
        rng = random.Random(seed)
        rng.shuffle(pool)
        out = []
        while len(out) < count:
            cycle = list(pool)
            rng.shuffle(cycle)
            out.extend(cycle)
        return out[:count]

    def adaptive_level(self, current_level, recent_accuracy):
        idx = LEVELS.index(current_level)
        if recent_accuracy >= 0.85 and idx < len(LEVELS)-1:
            return LEVELS[idx+1]
        if recent_accuracy < 0.50 and idx > 0:
            return LEVELS[idx-1]
        return current_level

    def xp_for_answer(self, correct, used_hint=False):
        if not correct:
            return 2
        return 10 if used_hint else 13

    def badge_for(self, total_correct, streak, perfect_rounds):
        badges = []
        if total_correct >= 1: badges.append("🌱 First Spark")
        if total_correct >= 10: badges.append("🧠 Curious Mind")
        if streak >= 5: badges.append("🔥 Hot Streak")
        if perfect_rounds >= 1: badges.append("💯 Perfect Mission")
        if total_correct >= 25: badges.append("🚀 STEAM Explorer")
        return badges

    def recommended_subject(self, mastery):
        return min(SUBJECTS, key=lambda s: mastery.get(s, 0))
