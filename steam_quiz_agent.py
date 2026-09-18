import random
from collections import defaultdict
import steam_quiz_db as db
from steam_question_bank import filter_questions,questions_by_ids

SUBJECTS=["Science","Technology","Engineering","Arts","Math"]
CORES=["Core 1","Core 2","Core 3"]

class Agent:
    def weak_subject(self,pid):
        m=db.mastery(pid); d=defaultdict(list)
        for r in m:d[r["subject"]].append(r["score"])
        return min(SUBJECTS,key=lambda s:sum(d[s])/len(d[s]) if d[s] else 0)

    def weak_skills(self,pid,limit=5):
        rows=sorted(db.mastery(pid),key=lambda r:r["score"])
        return rows[:limit]

    def prerequisite_status(self,pid,subject,grade):
        pool=filter_questions(subject,grade)
        mastery={(r["subject"],r["skill"]):r["score"] for r in db.mastery(pid)}
        out=[]
        for skill in sorted({q["skill"] for q in pool}):
            qs=[q for q in pool if q["skill"]==skill]
            prereq=qs[0].get("prerequisite","Foundations")
            score=round(mastery.get((subject,skill),0))
            out.append({"skill":skill,"prerequisite":prereq,"score":score,"unlocked":score>=60 or prereq=="Foundations"})
        return out

    def pick(self,pid,subject,grade,core,count,mode="Practice"):
        pool=filter_questions(subject,grade,core) or filter_questions(subject,grade)
        if mode=="Spaced Review":
            due=questions_by_ids(db.due_review_ids(pid,100))
            due=[q for q in due if q["subject"]==subject and q["grade"]==grade]
            if due: pool=due
        mastery={(r["subject"],r["skill"]):r["score"] for r in db.mastery(pid)}
        rnd=random.Random(pid*1000+len(db.attempts(pid))+count)
        pool=sorted(pool,key=lambda q:(mastery.get((q["subject"],q["skill"]),0),rnd.random()))
        if len(pool)<count:
            extra=filter_questions(subject,grade);rnd.shuffle(extra)
            for q in extra:
                if q not in pool:pool.append(q)
                if len(pool)>=count:break
        return pool[:count]

    def next_core(self,core,acc):
        i=CORES.index(core)
        return CORES[min(2,i+1)] if acc>=.85 else CORES[max(0,i-1)] if acc<.5 else core

    def badge_check(self,pid):
        a=db.attempts(pid,2000);p=db.get_profile(pid);correct=sum(x["correct"] for x in a)
        if a:db.award_badge(pid,"🌱 First Steps")
        if correct>=10:db.award_badge(pid,"🧠 Curious Mind")
        if p["answer_streak"]>=7:db.award_badge(pid,"🔥 Hot Streak")
        if p["daily_streak"]>=7:db.award_badge(pid,"📅 7-Day Streak")
        if len(a)>=25:db.award_badge(pid,"🏆 25 Questions")
        if p["xp"]>=500:db.award_badge(pid,"🦊 Explorer")
        if any(x["mode"]=="Puzzle Racer" and x["correct"] for x in a):db.award_badge(pid,"🏎️ Racer")
        # comeback: a question previously missed and later correct
        hist=defaultdict(list)
        for x in reversed(a):hist[x["question_id"]].append(x["correct"])
        if any(0 in seq and seq[-1]==1 for seq in hist.values()):db.award_badge(pid,"🔁 Comeback Kid")
