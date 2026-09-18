import time
import streamlit as st
from agent import STEAMQuizAgent, SUBJECTS, LEVELS

st.set_page_config(page_title="STEAM Quest", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")
agent = STEAMQuizAgent()

defaults = {
    "xp":0, "stars":0, "streak":0, "correct":0, "answered":0,
    "perfect_rounds":0, "mastery":{s:0 for s in SUBJECTS},
    "mission":None
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

icons={"Science":"🔬","Technology":"💻","Engineering":"🛠️","Arts":"🎨","Math":"➗"}

with st.sidebar:
    st.title("🚀 STEAM Quest")
    st.caption("Kid-safe quiz adventure")
    profile=st.text_input("Explorer name", "Young Explorer")
    grade=st.selectbox("Grade band", ["Grades 2–3","Grades 4–5","Grades 6–7"], index=1)
    session_limit=st.slider("Parent session limit",5,45,20,5)
    timed=st.toggle("Timed mission",False)
    st.divider()
    st.metric("XP",st.session_state.xp)
    st.metric("Stars",st.session_state.stars)
    st.metric("Streak",st.session_state.streak)

st.title(f"Welcome, {profile}! 🧪🤖🎨📐")
st.write("Pick a STEAM world, complete missions, earn XP and stars, unlock badges, and level up.")

level=1+st.session_state.xp//100
character="🥚 Spark" if level<2 else "🐣 Builder" if level<4 else "🦊 Inventor" if level<7 else "🦸 STEAM Hero"
accuracy=(st.session_state.correct/st.session_state.answered*100) if st.session_state.answered else 0

a,b,c,d=st.columns(4)
a.metric("Level",level); b.metric("Character",character); c.metric("Answered",st.session_state.answered); d.metric("Accuracy",f"{accuracy:.0f}%")

st.header("🌎 Five STEAM Worlds")
cols=st.columns(5)
for col,subject in zip(cols,SUBJECTS):
    with col:
        st.subheader(f"{icons[subject]} {subject}")
        st.progress(st.session_state.mastery[subject]/100)
        st.caption(f"Mastery {st.session_state.mastery[subject]}%")

st.divider()
st.header("🎯 Start a Quiz Mission")
c1,c2,c3=st.columns(3)
with c1: subject=st.selectbox("Subject",SUBJECTS)
with c2: difficulty=st.selectbox("Difficulty",LEVELS)
with c3: count=st.selectbox("Questions",[3,5,10],index=1)

rec=agent.recommended_subject(st.session_state.mastery)
st.info(f"🤖 Agent recommendation: try **{rec}** next because it has your lowest mastery.")

if st.button("🚀 Launch mission",use_container_width=True):
    st.session_state.mission={
        "subject":subject,
        "difficulty":difficulty,
        "questions":agent.question_set(subject,difficulty,count,seed=st.session_state.answered+11),
        "index":0,
        "round_correct":0,
        "used_hint":set(),
        "start_time":time.time(),
        "complete":False,
        "feedback":None
    }
    st.rerun()

m=st.session_state.mission
if m and not m["complete"]:
    idx=m["index"]; q=m["questions"][idx]
    st.divider()
    st.subheader(f"{icons[m['subject']]} {m['subject']} · {m['difficulty']}")
    st.caption(f"Question {idx+1} of {len(m['questions'])}")
    if timed:
        st.caption(f"⏱️ {int(time.time()-m['start_time'])} sec")

    st.markdown(f"### {q['q']}")
    choice=st.radio("Choose one:",q["options"],key=f"choice_{idx}_{m['subject']}")

    if st.button("💡 Hint",key=f"hint_{idx}"):
        m["used_hint"].add(idx)
        st.session_state.mission=m
    if idx in m["used_hint"]:
        st.info(q["hint"])

    if st.button("✅ Check answer",key=f"check_{idx}",use_container_width=True):
        ok=choice==q["answer"]
        st.session_state.answered+=1
        xp=agent.xp_for_answer(ok,idx in m["used_hint"])
        st.session_state.xp+=xp
        if ok:
            st.session_state.correct+=1
            st.session_state.streak+=1
            st.session_state.stars+=1
            m["round_correct"]+=1
            m["feedback"]=f"🎉 Correct! +{xp} XP · +1 ⭐\n\nWhy: {q['why']}"
        else:
            st.session_state.streak=0
            m["feedback"]=f"Good try. Best answer: **{q['answer']}**\n\nWhy: {q['why']}"
        st.session_state.mission=m

    if m.get("feedback"):
        st.success(m["feedback"]) if "Correct!" in m["feedback"] else st.warning(m["feedback"])
        if st.button("Next question"):
            if idx+1>=len(m["questions"]):
                score=m["round_correct"]
                pct=score/len(m["questions"])
                if pct==1:
                    st.session_state.perfect_rounds+=1
                old=st.session_state.mastery[m["subject"]]
                st.session_state.mastery[m["subject"]]=max(0,min(100,round(old*0.75+pct*100*0.25)))
                m["suggested"]=agent.adaptive_level(m["difficulty"],pct)
                m["complete"]=True
            else:
                m["index"]+=1
                m["feedback"]=None
            st.session_state.mission=m
            st.rerun()

if m and m.get("complete"):
    st.divider()
    st.header("🏁 Mission Complete")
    score=m["round_correct"]; total=len(m["questions"])
    x,y,z=st.columns(3)
    x.metric("Score",f"{score}/{total}")
    y.metric("Mastery",f"{st.session_state.mastery[m['subject']]}%")
    z.metric("Next difficulty",m["suggested"])
    st.write("Adaptive rule: **85%+ → level up · 50–84% → stay · below 50% → step down when possible**.")

st.divider()
st.header("🏅 Badges")
badges=agent.badge_for(st.session_state.correct,st.session_state.streak,st.session_state.perfect_rounds)
st.write(" · ".join(badges) if badges else "Complete your first correct answer to unlock a badge.")

st.header("🎁 Parent Reward Catalog")
r1,r2,r3=st.columns(3)
r1.markdown("### 📚 Pick a new book\n120 ⭐")
r2.markdown("### 🍕 Family pizza night\n150 ⭐")
r3.markdown("### 🎮 Bonus game time\n80 ⭐")
st.caption("Parents can replace these with family-approved rewards.")

st.divider()
st.header("🧠 Agent Loop")
st.code("""
Pick STEAM subject
      ↓
Pick difficulty
      ↓
Ask objective quiz question
      ↓
Optional hint
      ↓
Grade answer
      ↓
Explain WHY
      ↓
Award XP + stars + streak
      ↓
Update subject mastery
      ↓
Adapt difficulty
      ↓
Recommend weakest STEAM world
      ↓
Next mission
""",language="text")

st.header("👨‍👩‍👧 Parent View")
cols=st.columns(5)
for col,s in zip(cols,SUBJECTS):
    col.metric(s,f"{st.session_state.mastery[s]}%")

st.caption("Starter version stores progress in the Streamlit session only.")
