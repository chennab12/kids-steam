import random
from collections import defaultdict
import db
from question_bank import filter_questions
SUBJECTS=["Science","Technology","Engineering","Arts","Math"]; CORES=["Core 1","Core 2","Core 3"]
class Agent:
    def weak_subject(self,pid):
        m=db.mastery(pid); d=defaultdict(list)
        for r in m:d[r["subject"]].append(r["score"])
        return min(SUBJECTS,key=lambda s:sum(d[s])/len(d[s]) if d[s] else 0)
    def pick(self,pid,subject,grade,core,count,review=False):
        pool=filter_questions(subject,grade,core) or filter_questions(subject,grade)
        if review:
            ids=set(db.wrong_ids(pid)); miss=[q for q in pool if q["id"] in ids]
            if miss: pool=miss
        mm={(r["subject"],r["skill"]):r["score"] for r in db.mastery(pid)}
        rnd=random.Random(pid*1000+len(db.attempts(pid)))
        pool=sorted(pool,key=lambda q:(mm.get((q["subject"],q["skill"]),0),rnd.random()))
        if len(pool)<count:
            extra=filter_questions(subject,grade); rnd.shuffle(extra)
            for q in extra:
                if q not in pool: pool.append(q)
                if len(pool)>=count: break
        return pool[:count]
    def next_core(self,core,acc):
        i=CORES.index(core)
        return CORES[min(2,i+1)] if acc>=.85 else CORES[max(0,i-1)] if acc<.5 else core
    def badge_check(self,pid):
        a=db.attempts(pid); p=db.get_profile(pid); correct=sum(x["correct"] for x in a)
        if a: db.award_badge(pid,"🌱 First Steps")
        if correct>=10: db.award_badge(pid,"🧠 Curious Mind")
        if p["streak"]>=7: db.award_badge(pid,"🔥 Hot Streak")
        if len(a)>=25: db.award_badge(pid,"🏆 25 Questions")
        if p["xp"]>=500: db.award_badge(pid,"🦊 Explorer")
