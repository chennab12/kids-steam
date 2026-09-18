import time,streamlit as st
import steam_quiz_db as db
from steam_quiz_agent import Agent,SUBJECTS,CORES
from steam_question_bank import skills_for,projects_for

st.set_page_config(page_title="STEAM Mesh V3",page_icon="🦊",layout="wide")
db.init_db();agent=Agent()

for k,v in {"pid":None,"parent":False,"mission":None,"session_start":time.time()}.items():
    if k not in st.session_state:st.session_state[k]=v

profiles=db.profiles()
if st.session_state.pid is None:
    st.title("🦊 STEAM Mesh V3");st.subheader("Who is learning today?")
    cols=st.columns(min(4,len(profiles)+1))
    for c,p in zip(cols,profiles):
        with c:
            st.markdown(f"## {p['avatar']}");st.write(f"**{p['name']}** · Grade {p['grade']}")
            st.caption(f"Level {1+p['xp']//100} · {p['xp']} XP · 🔥 {p['daily_streak']} day streak")
            if st.button("Enter",key=f"p{p['id']}",use_container_width=True):
                st.session_state.pid=p["id"];st.session_state.session_start=time.time();st.rerun()
    with cols[-1]:
        st.markdown("## 🔒");st.write("**Parent**")
        if st.button("Parent sign in"):st.session_state.parent_login=True
    if st.session_state.get("parent_login"):
        pin=st.text_input("PIN",type="password")
        if st.button("Unlock"):
            if db.verify_pin(pin):st.session_state.parent=True;st.session_state.pid=profiles[0]["id"];st.rerun()
            else:st.error("Wrong PIN")
    st.caption("First-run PIN: 2468. Change it in Parent Center.")
    st.stop()

pid=st.session_state.pid;p=db.get_profile(pid);agent.badge_check(pid);p=db.get_profile(pid)
elapsed=(time.time()-st.session_state.session_start)/60
if elapsed>=p["session_limit"]:
    st.warning("⏰ Session limit reached.")
    if st.button("Finish session"):st.session_state.pid=None;st.session_state.mission=None;st.rerun()
    st.stop()
elif elapsed>=p["break_reminder"]:st.info("💧 Break reminder: stretch, blink, and return refreshed.")

with st.sidebar:
    st.title(f"{p['avatar']} {p['name']}")
    st.caption(f"Grade {p['grade']} · Level {1+p['xp']//100}")
    st.metric("XP",p["xp"]);st.metric("Stars",p["stars"]);st.metric("Daily streak",f"{p['daily_streak']} days")
    page=st.radio("Navigate",["Home","Skill Map","Practice","Spaced Review","Timed Test","Puzzle Racer","Projects","Family Feed","Rewards","Badges","Parent Center"])
    if st.button("Switch profile"):st.session_state.pid=None;st.session_state.parent=False;st.session_state.mission=None;st.rerun()

def subject_mastery(s):
    vals=[x["score"] for x in db.mastery(pid) if x["subject"]==s]
    return round(sum(vals)/len(vals)) if vals else 0

if page=="Home":
    st.title("Adaptive STEAM learning")
    ats=db.attempts(pid);acc=100*sum(x["correct"] for x in ats)/len(ats) if ats else 0
    a,b,c,d=st.columns(4);a.metric("Level",1+p["xp"]//100);b.metric("Accuracy",f"{acc:.0f}%");c.metric("Questions",len(ats));d.metric("Daily streak",f"{p['daily_streak']} 🔥")
    cols=st.columns(5);icons={"Science":"🔬","Technology":"💻","Engineering":"🛠️","Arts":"🎨","Math":"➗"}
    for c,s in zip(cols,SUBJECTS):
        with c:st.markdown(f"### {icons[s]} {s}");st.progress(subject_mastery(s)/100);st.caption(f"{subject_mastery(s)}% mastery")
    st.info(f"🤖 Recommended next world: **{agent.weak_subject(pid)}**")
    due=len(db.due_review_ids(pid,100))
    if due:st.warning(f"🔁 You have **{due}** spaced-review question(s) due.")
    ws=agent.weak_skills(pid,3)
    if ws:
        st.subheader("Skills to strengthen")
        for x in ws:st.write(f"• {x['subject']} → {x['skill']}: {x['score']:.0f}%")

elif page=="Skill Map":
    st.title("🗺️ Skill Map")
    subject=st.selectbox("Subject",SUBJECTS)
    rows=agent.prerequisite_status(pid,subject,p["grade"])
    for r in rows:
        icon="✅" if r["score"]>=90 else "🟡" if r["score"]>=60 else "🔒"
        st.write(f"{icon} **{r['skill']}** · Mastery {r['score']}% · prerequisite: {r['prerequisite']}")
        st.progress(r["score"]/100)

def run_mission(mode):
    st.title(mode)
    a,b,c,d=st.columns(4)
    with a:s=st.selectbox("Subject",SUBJECTS,key=mode+"s")
    with b:core=st.selectbox("Core",CORES,index=1,key=mode+"c")
    with c:n=st.selectbox("Questions",[5,10,20],index=1,key=mode+"n")
    with d:mins=st.selectbox("Minutes",[5,10,15,20],index=1,key=mode+"m") if mode in ["Timed Test","Puzzle Racer"] else None
    st.caption("Grade skills: "+", ".join(skills_for(s,p["grade"])[:10]))
    if st.button("Launch",key=mode+"launch",use_container_width=True):
        qs=agent.pick(pid,s,p["grade"],core,n,mode)
        st.session_state.mission={"mode":mode,"subject":s,"qs":qs,"i":0,"correct":0,"core":core,"start":time.time(),"qstart":time.time(),"hint":False,"fb":None,"limit":mins*60 if mins else None}
        st.rerun()
    m=st.session_state.mission
    if not m or m["mode"]!=mode:return
    if m.get("done"):
        total=len(m["qs"]);acc=m["correct"]/total if total else 0;elapsed_sec=time.time()-m["start"]
        x,y,z=st.columns(3);x.metric("Score",f"{m['correct']}/{total}");y.metric("Accuracy",f"{acc*100:.0f}%");z.metric("Next core",agent.next_core(m["core"],acc))
        if mode=="Puzzle Racer":
            best=db.racer_best(pid,m["subject"],p["grade"])
            improved=db.save_racer(pid,m["subject"],p["grade"],elapsed_sec,acc)
            st.metric("Your time",f"{elapsed_sec:.1f}s")
            if improved:st.success("🏁 New personal best!")
            elif best:st.caption(f"Personal best: {best['best_seconds']:.1f}s at {best['best_accuracy']*100:.0f}% accuracy")
        if st.button("New mission",key=mode+"new"):st.session_state.mission=None;st.rerun()
        return
    if m["limit"] and time.time()-m["start"]>=m["limit"]:m["done"]=True;st.session_state.mission=m;st.rerun()
    q=m["qs"][m["i"]];st.caption(f"{m['i']+1}/{len(m['qs'])} · Grade {q['grade']} · {q['skill']} · {q['difficulty']}")
    if m["limit"]:
        rem=max(0,int(m["limit"]-(time.time()-m["start"])));st.metric("Time left",f"{rem//60}:{rem%60:02d}")
    st.markdown(f"## {q['prompt']}");choice=st.radio("Choose one",q["options"],key=mode+q["id"]+str(m["i"]))
    if st.button("💡 Hint",key=mode+"hint"):m["hint"]=True;st.session_state.mission=m
    if m["hint"]:st.info(q["hint"])
    if not m["fb"] and st.button("Check answer",key=mode+"check",use_container_width=True):
        ok=choice==q["answer"];xp,_=db.add_attempt(pid,q,ok,m["hint"],time.time()-m["qstart"],mode)
        if ok:m["correct"]+=1
        m["fb"]=(ok,xp);st.session_state.mission=m;st.rerun()
    if m["fb"]:
        ok,xp=m["fb"];st.success(f"🎉 Correct · +{xp} XP · +1 ⭐") if ok else st.warning(f"Good try. Best answer: **{q['answer']}**")
        st.write("**Why:** "+q["explanation"])
        if st.button("Next",key=mode+"next"):
            if m["i"]+1>=len(m["qs"]):m["done"]=True
            else:m["i"]+=1;m["qstart"]=time.time();m["hint"]=False;m["fb"]=None
            st.session_state.mission=m;st.rerun()

if page=="Practice":run_mission("Practice")
elif page=="Spaced Review":run_mission("Spaced Review")
elif page=="Timed Test":run_mission("Timed Test")
elif page=="Puzzle Racer":run_mission("Puzzle Racer")

elif page=="Projects":
    st.title("🛠️ Hands-on STEAM Projects")
    subject=st.selectbox("Project world",SUBJECTS)
    plist=projects_for(p["grade"],subject)
    done={x["project_id"] for x in db.completed_projects(pid)}
    if not plist:st.info("No project in this grade/subject yet.")
    for pr in plist:
        with st.expander(("✅ " if pr["id"] in done else "⬜ ")+pr["title"]):
            st.write("**Goal:** "+pr["goal"]);st.write("**Materials:** "+", ".join(pr["materials"]))
            st.write("**Steps:**");[st.write(f"{i+1}. {step}") for i,step in enumerate(pr["steps"])]
            st.write("**Measure:** "+pr["measure"]);st.write("**Reflect:** "+pr["reflection"])
            notes=st.text_area("Project notes",key=pr["id"]+"notes")
            if pr["id"] not in done and st.button("Mark project complete",key=pr["id"]):
                if db.complete_project(pid,pr["id"],notes):st.success("Project complete! +50 XP and +5 ⭐");st.rerun()

elif page=="Family Feed":
    st.title("👥 Family Feed")
    for item in db.family_feed(30):
        icon="🎉" if item["correct"] else "🌱";verb="solved" if item["correct"] else "practiced"
        st.write(f"{icon} {item['avatar']} **{item['name']}** {verb} **{item['skill']}** in {item['subject']}.")

elif page=="Rewards":
    st.title("🎁 Rewards");st.write(f"Balance: **{p['stars']} ⭐**")
    for r in db.rewards():
        a,b=st.columns([3,1]);a.write(f"**{r['name']}** — {r['stars_cost']} ⭐")
        if b.button("Redeem",key=str(r["id"]),disabled=p["stars"]<r["stars_cost"]):
            if db.redeem(pid,r):st.success("Requested. Parent approval pending.");st.rerun()

elif page=="Badges":
    st.title("🏅 Badges");have={x["badge"] for x in db.badges(pid)}
    catalog=["🌱 First Steps","🧠 Curious Mind","🔥 Hot Streak","📅 7-Day Streak","🏆 25 Questions","🦊 Explorer","🏎️ Racer","🔁 Comeback Kid"]
    for b in catalog:st.write(("✅ " if b in have else "🔒 ")+b)

elif page=="Parent Center":
    st.title("🛡️ Parent Center")
    if not st.session_state.parent:
        pin=st.text_input("Family PIN",type="password")
        if st.button("Unlock"):
            if db.verify_pin(pin):st.session_state.parent=True;st.rerun()
            else:st.error("Wrong PIN")
        st.stop()
    t1,t2,t3,t4,t5=st.tabs(["Weekly Analytics","Profiles","Controls","Rewards","Security"])
    with t1:
        stats=db.weekly_stats(pid);cur=stats["current"];prev=stats["previous"]
        a,b,c,d=st.columns(4);a.metric("Questions",cur["n"],delta=cur["n"]-prev["n"]);b.metric("Accuracy",f"{cur['acc']:.0f}%",delta=f"{cur['acc']-prev['acc']:.0f} pts");c.metric("Learning days",cur["learning_days"]);d.metric("Avg answer time",f"{cur['avg_seconds']:.1f}s")
        st.subheader("Current weak skills")
        for x in agent.weak_skills(pid,5):st.write(f"• {x['subject']} → {x['skill']}: {x['score']:.0f}%")
    with t2:
        for x in db.profiles():st.write(f"{x['avatar']} **{x['name']}** · Grade {x['grade']} · {x['xp']} XP · {x['daily_streak']} day streak")
        name=st.text_input("New child name");grade=st.selectbox("Grade",[2,3,4,5,6,7],index=2);avatar=st.selectbox("Avatar",["🦊","🐸","🐼","🤖","🦄"])
        if st.button("Add profile") and name.strip():db.add_profile(name.strip(),grade,avatar);st.rerun()
    with t3:
        lim=st.slider("Session limit",5,60,p["session_limit"],5);br=st.slider("Break reminder",5,45,min(45,p["break_reminder"]),5);night=st.toggle("Night mode",bool(p["night_mode"]))
        if st.button("Save controls"):db.save_controls(pid,lim,br,night);st.success("Saved");st.rerun()
    with t4:
        rn=st.text_input("Reward name");cost=st.number_input("Star cost",10,1000,100,10)
        if st.button("Add reward") and rn.strip():db.add_reward(rn.strip(),int(cost));st.rerun()
        for rr in db.redemptions():
            a,b,c=st.columns([3,1,1]);a.write(f"**{rr['name']}** requested {rr['reward_name']} · {rr['stars_cost']} ⭐ · {rr['status']}")
            if rr["status"]=="requested":
                if b.button("Approve",key="ap"+str(rr["id"])):db.set_redemption_status(rr["id"],"approved");st.rerun()
                if c.button("Decline",key="de"+str(rr["id"])):db.set_redemption_status(rr["id"],"declined");st.rerun()
    with t5:
        st.warning("Change first-run PIN 2468.");np=st.text_input("New PIN",type="password")
        if st.button("Change PIN"):
            if len(np)>=4:db.change_pin(np);st.success("PIN changed")
            else:st.error("Use at least 4 characters")
