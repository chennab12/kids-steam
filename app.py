import time,streamlit as st
import steam_quiz_db as db
from steam_quiz_agent import Agent, SUBJECTS, CORES
from steam_question_bank import skills_for
st.set_page_config(page_title="STEAM Mesh",page_icon="🦊",layout="wide")
db.init_db(); agent=Agent()
for k,v in {"pid":None,"parent":False,"mission":None,"session_start":time.time()}.items():
    if k not in st.session_state: st.session_state[k]=v
profiles=db.profiles()
if st.session_state.pid is None:
    st.title("🦊 STEAM Mesh"); st.subheader("Who is learning today?")
    cols=st.columns(min(4,len(profiles)+1))
    for c,p in zip(cols,profiles):
        with c:
            st.markdown(f"## {p['avatar']}"); st.write(f"**{p['name']}** · Grade {p['grade']}"); st.caption(f"Lv {1+p['xp']//100} · {p['xp']} XP")
            if st.button("Enter",key=f"p{p['id']}",use_container_width=True): st.session_state.pid=p["id"];st.session_state.session_start=time.time();st.rerun()
    with cols[-1]:
        st.markdown("## 🔒"); st.write("**Parent**")
        if st.button("Parent sign in"):
            st.session_state.parent_login=True
    if st.session_state.get("parent_login"):
        pin=st.text_input("PIN",type="password")
        if st.button("Unlock"):
            if db.verify_pin(pin): st.session_state.parent=True;st.session_state.pid=profiles[0]["id"];st.rerun()
            else: st.error("Wrong PIN")
    st.caption("First-run demo PIN: 2468. Change it in Parent Center.")
    st.stop()
pid=st.session_state.pid;p=db.get_profile(pid);agent.badge_check(pid);p=db.get_profile(pid)
elapsed=(time.time()-st.session_state.session_start)/60
if elapsed>=p["session_limit"]:
    st.warning("⏰ Session limit reached.")
    if st.button("Finish session"): st.session_state.pid=None;st.session_state.mission=None;st.rerun()
    st.stop()
elif elapsed>=p["break_reminder"]: st.info("💧 Break reminder: stretch, blink, and return refreshed.")
with st.sidebar:
    st.title(f"{p['avatar']} {p['name']}");st.caption(f"Grade {p['grade']} · Level {1+p['xp']//100}")
    st.metric("XP",p["xp"]);st.metric("Stars",p["stars"]);st.metric("Streak",p["streak"])
    page=st.radio("Navigate",["Home","Practice","Timed Test","Review Missed","Family Feed","Rewards","Badges","Parent Center"])
    if st.button("Switch profile"): st.session_state.pid=None;st.session_state.parent=False;st.session_state.mission=None;st.rerun()
def sm(s):
    r=[x["score"] for x in db.mastery(pid) if x["subject"]==s]; return round(sum(r)/len(r)) if r else 0
if page=="Home":
    st.title("One curious STEAM universe")
    st.write("Profiles, mastery, timed missions, rewards, badges, streaks, and adaptive practice.")
    a,b,c,d=st.columns(4);ats=db.attempts(pid);acc=100*sum(x["correct"] for x in ats)/len(ats) if ats else 0
    level=1+p["xp"]//100
    stage="🥚 Hatchling" if level<3 else "🐣 Sprout" if level<5 else "🦊 Explorer" if level<8 else "🦸 STEAM Hero"
    a.metric("Character",stage);a.caption(f"Level {level}")
    b.metric("Accuracy",f"{acc:.0f}%");c.metric("Questions",len(ats));d.metric("Stars",p["stars"])
    icons={"Science":"🔬","Technology":"💻","Engineering":"🛠️","Arts":"🎨","Math":"➗"}
    cols=st.columns(5)
    for c,s in zip(cols,SUBJECTS):
        with c: st.markdown(f"### {icons[s]} {s}");st.progress(sm(s)/100);st.caption(f"Mastery {sm(s)}%")
    st.info(f"🤖 Recommended next world: **{agent.weak_subject(pid)}**")
def mission(mode):
    st.title(mode)
    a,b,c,d=st.columns(4)
    with a:s=st.selectbox("Subject",SUBJECTS)
    with b:core=st.selectbox("Core",CORES,index=1)
    with c:n=st.selectbox("Questions",[5,10,20],index=1)
    with d:mins=st.selectbox("Minutes",[5,10,15,20],index=1) if mode=="Timed Test" else None
    st.caption("Grade skills: "+", ".join(skills_for(s,p["grade"])[:10]))
    if st.button("Launch",use_container_width=True):
        st.session_state.mission={"mode":mode,"qs":agent.pick(pid,s,p["grade"],core,n,mode=="Review Missed"),"i":0,"correct":0,"core":core,"start":time.time(),"qstart":time.time(),"hint":False,"fb":None,"limit":mins*60 if mins else None};st.rerun()
    m=st.session_state.mission
    if not m or m["mode"]!=mode:return
    if m.get("done"):
        total=len(m["qs"]);acc=m["correct"]/total if total else 0
        x,y,z=st.columns(3);x.metric("Score",f"{m['correct']}/{total}");y.metric("Accuracy",f"{acc*100:.0f}%");z.metric("Next core",agent.next_core(m["core"],acc))
        if st.button("New mission"):st.session_state.mission=None;st.rerun()
        return
    if m["limit"] and time.time()-m["start"]>=m["limit"]:m["done"]=True;st.session_state.mission=m;st.rerun()
    q=m["qs"][m["i"]];st.caption(f"{m['i']+1}/{len(m['qs'])} · Grade {q['grade']} · {q['skill']} · {q['difficulty']}")
    if m["limit"]:
        rem=max(0,int(m["limit"]-(time.time()-m["start"])));st.metric("Time left",f"{rem//60}:{rem%60:02d}")
    st.markdown(f"## {q['prompt']}");choice=st.radio("Choose one",q["options"],key=q["id"]+str(m["i"]))
    if st.button("💡 Hint"):m["hint"]=True;st.session_state.mission=m
    if m["hint"]:st.info(q["hint"])
    if not m["fb"] and st.button("Check answer",use_container_width=True):
        ok=choice==q["answer"];xp,_=db.add_attempt(pid,q,ok,m["hint"],time.time()-m["qstart"]);db.set_streak(pid,p["streak"]+1 if ok else 0)
        if ok:m["correct"]+=1
        m["fb"]=(ok,xp);st.session_state.mission=m;st.rerun()
    if m["fb"]:
        ok,xp=m["fb"]
        st.success(f"🎉 Correct · +{xp} XP · +1 ⭐") if ok else st.warning(f"Good try. Best answer: **{q['answer']}**")
        st.write("**Why:** "+q["explanation"])
        if st.button("Next"):
            if m["i"]+1>=len(m["qs"]):m["done"]=True
            else:m["i"]+=1;m["qstart"]=time.time();m["hint"]=False;m["fb"]=None
            st.session_state.mission=m;st.rerun()
if page=="Practice":mission("Practice")
elif page=="Timed Test":mission("Timed Test")
elif page=="Review Missed":mission("Review Missed")
elif page=="Family Feed":
    st.title("👥 Family Feed")
    st.caption("Private family-only learning activity. No public social network in this starter.")
    feed=db.family_feed(30)
    if not feed: st.info("Complete a quiz to create the first family update.")
    for item in feed:
        icon="🎉" if item["correct"] else "🌱"
        result="solved" if item["correct"] else "practiced"
        st.write(f"{icon} {item['avatar']} **{item['name']}** {result} **{item['skill']}** in {item['subject']}.")
elif page=="Rewards":
    st.title("🎁 Rewards");st.write(f"Balance: **{p['stars']} ⭐**")
    for r in db.rewards():
        a,b=st.columns([3,1]);a.write(f"**{r['name']}** — {r['stars_cost']} ⭐")
        if b.button("Redeem",key=str(r["id"]),disabled=p["stars"]<r["stars_cost"]):
            if db.redeem(pid,r):st.success("Redeemed. Ask your parent to confirm.");st.rerun()
elif page=="Badges":
    st.title("🏅 Badges");have={x["badge"] for x in db.badges(pid)}
    for b in ["🌱 First Steps","🧠 Curious Mind","🔥 Hot Streak","🏆 25 Questions","🦊 Explorer"]:st.write(("✅ " if b in have else "🔒 ")+b)
elif page=="Parent Center":
    st.title("🛡️ Parent Center")
    if not st.session_state.parent:
        pin=st.text_input("Family PIN",type="password")
        if st.button("Unlock"):
            if db.verify_pin(pin):st.session_state.parent=True;st.rerun()
            else:st.error("Wrong PIN")
        st.stop()
    t1,t2,t3,t4=st.tabs(["Profiles","Controls","Rewards","Security"])
    with t1:
        for x in db.profiles():st.write(f"{x['avatar']} **{x['name']}** · Grade {x['grade']} · {x['xp']} XP")
        name=st.text_input("New child name");grade=st.selectbox("Grade",[2,3,4,5,6,7],index=2);avatar=st.selectbox("Avatar",["🦊","🐸","🐼","🤖","🦄"])
        if st.button("Add profile") and name.strip():db.add_profile(name.strip(),grade,avatar);st.rerun()
    with t2:
        lim=st.slider("Session limit",5,60,p["session_limit"],5);br=st.slider("Break reminder",5,45,min(45,p["break_reminder"]),5);night=st.toggle("Night mode",bool(p["night_mode"]))
        if st.button("Save controls"):db.save_controls(pid,lim,br,night);st.success("Saved");st.rerun()
    with t3:
        rn=st.text_input("Reward name");cost=st.number_input("Star cost",10,1000,100,10)
        if st.button("Add reward") and rn.strip():db.add_reward(rn.strip(),int(cost));st.rerun()
        for r in db.rewards():st.write(f"• {r['name']} — {r['stars_cost']} ⭐")
        st.divider(); st.subheader("Redemption requests")
        for rr in db.redemptions():
            a,b,c=st.columns([3,1,1]); a.write(f"**{rr['name']}** requested {rr['reward_name']} · {rr['stars_cost']} ⭐ · {rr['status']}")
            if rr["status"]=="requested":
                if b.button("Approve",key=f"ap{rr['id']}"): db.set_redemption_status(rr["id"],"approved"); st.rerun()
                if c.button("Decline",key=f"de{rr['id']}"): db.set_redemption_status(rr["id"],"declined"); st.rerun()
    with t4:
        st.warning("Change demo PIN 2468.");np=st.text_input("New PIN",type="password")
        if st.button("Change PIN"):
            if len(np)>=4:db.change_pin(np);st.success("PIN changed")
            else:st.error("Use at least 4 characters")
