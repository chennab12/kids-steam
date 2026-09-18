import sqlite3, hashlib, datetime
from pathlib import Path
DB=Path(__file__).parent/"data/steam_mesh.db"

def cx():
    c=sqlite3.connect(DB,check_same_thread=False); c.row_factory=sqlite3.Row; return c

def hp(pin): return hashlib.sha256(("steam-mesh-v3:"+pin).encode()).hexdigest()

def init_db():
    c=cx(); c.executescript("""
    CREATE TABLE IF NOT EXISTS family(id INTEGER PRIMARY KEY,pin_hash TEXT);
    CREATE TABLE IF NOT EXISTS profiles(
      id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,grade INTEGER,avatar TEXT,
      xp INTEGER DEFAULT 0,stars INTEGER DEFAULT 0,answer_streak INTEGER DEFAULT 0,
      daily_streak INTEGER DEFAULT 0,last_learning_date TEXT,
      session_limit INTEGER DEFAULT 20,break_reminder INTEGER DEFAULT 15,night_mode INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS attempts(
      id INTEGER PRIMARY KEY AUTOINCREMENT,profile_id INTEGER,question_id TEXT,subject TEXT,skill TEXT,subskill TEXT,
      grade INTEGER,correct INTEGER,used_hint INTEGER,seconds REAL,mode TEXT DEFAULT 'Practice',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS mastery(
      profile_id INTEGER,subject TEXT,skill TEXT,subskill TEXT,score REAL DEFAULT 0,attempts INTEGER DEFAULT 0,
      PRIMARY KEY(profile_id,subject,skill,subskill));
    CREATE TABLE IF NOT EXISTS review_queue(
      profile_id INTEGER,question_id TEXT,next_review TEXT,interval_days INTEGER DEFAULT 1,ease REAL DEFAULT 2.0,
      repetitions INTEGER DEFAULT 0,last_result INTEGER DEFAULT 0,
      PRIMARY KEY(profile_id,question_id));
    CREATE TABLE IF NOT EXISTS rewards(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,stars_cost INTEGER,active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS redemptions(id INTEGER PRIMARY KEY AUTOINCREMENT,profile_id INTEGER,reward_name TEXT,stars_cost INTEGER,status TEXT DEFAULT 'requested',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS badges(profile_id INTEGER,badge TEXT,earned_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(profile_id,badge));
    CREATE TABLE IF NOT EXISTS racer_scores(profile_id INTEGER,subject TEXT,grade INTEGER,best_seconds REAL,best_accuracy REAL,updated_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(profile_id,subject,grade));
    CREATE TABLE IF NOT EXISTS project_completions(profile_id INTEGER,project_id TEXT,completed_at TEXT DEFAULT CURRENT_TIMESTAMP,notes TEXT,PRIMARY KEY(profile_id,project_id));
    """)
    # migrations from V2
    cols={r["name"] for r in c.execute("PRAGMA table_info(profiles)")}
    for name,definition in [
        ("answer_streak","INTEGER DEFAULT 0"),("daily_streak","INTEGER DEFAULT 0"),("last_learning_date","TEXT")
    ]:
        if name not in cols: c.execute(f"ALTER TABLE profiles ADD COLUMN {name} {definition}")
    acols={r["name"] for r in c.execute("PRAGMA table_info(attempts)")}
    for name,definition in [("subskill","TEXT DEFAULT ''"),("mode","TEXT DEFAULT 'Practice'")]:
        if name not in acols:c.execute(f"ALTER TABLE attempts ADD COLUMN {name} {definition}")
    mcols={r["name"] for r in c.execute("PRAGMA table_info(mastery)")}
    if "subskill" not in mcols:
        # Old PK cannot be altered safely; preserve old rows and rebuild.
        c.executescript("""
        ALTER TABLE mastery RENAME TO mastery_old;
        CREATE TABLE mastery(profile_id INTEGER,subject TEXT,skill TEXT,subskill TEXT,score REAL DEFAULT 0,attempts INTEGER DEFAULT 0,PRIMARY KEY(profile_id,subject,skill,subskill));
        INSERT OR IGNORE INTO mastery(profile_id,subject,skill,subskill,score,attempts)
        SELECT profile_id,subject,skill,skill,score,attempts FROM mastery_old;
        DROP TABLE mastery_old;
        """)
    if not c.execute("SELECT 1 FROM family WHERE id=1").fetchone(): c.execute("INSERT INTO family VALUES(1,?)",(hp("2468"),))
    if not c.execute("SELECT 1 FROM profiles LIMIT 1").fetchone(): c.execute("INSERT INTO profiles(name,grade,avatar) VALUES('Explorer',4,'🦊')")
    if not c.execute("SELECT 1 FROM rewards LIMIT 1").fetchone():
        c.executemany("INSERT INTO rewards(name,stars_cost) VALUES(?,?)",[("Bonus game time",80),("Family pizza night",120),("Pick a new book",150),("Choose family movie",100)])
    c.commit(); c.close()

def verify_pin(pin):
    c=cx(); r=c.execute("SELECT pin_hash FROM family WHERE id=1").fetchone(); c.close(); return bool(r and r["pin_hash"]==hp(pin))
def change_pin(pin):
    c=cx(); c.execute("UPDATE family SET pin_hash=? WHERE id=1",(hp(pin),)); c.commit(); c.close()
def profiles():
    c=cx();r=[dict(x) for x in c.execute("SELECT * FROM profiles ORDER BY id")];c.close();return r
def get_profile(pid):
    c=cx();r=c.execute("SELECT * FROM profiles WHERE id=?",(pid,)).fetchone();c.close();return dict(r)
def add_profile(name,grade,avatar):
    c=cx();c.execute("INSERT INTO profiles(name,grade,avatar) VALUES(?,?,?)",(name,grade,avatar));c.commit();c.close()
def save_controls(pid,limit,br,night):
    c=cx();c.execute("UPDATE profiles SET session_limit=?,break_reminder=?,night_mode=? WHERE id=?",(limit,br,int(night),pid));c.commit();c.close()

def _update_daily_streak(c,pid):
    p=c.execute("SELECT daily_streak,last_learning_date FROM profiles WHERE id=?",(pid,)).fetchone()
    today=datetime.date.today(); last=p["last_learning_date"]
    streak=p["daily_streak"] or 0
    if not last: streak=1
    else:
        d=datetime.date.fromisoformat(last); delta=(today-d).days
        if delta==1: streak+=1
        elif delta>1: streak=1
    c.execute("UPDATE profiles SET daily_streak=?,last_learning_date=? WHERE id=?",(streak,today.isoformat(),pid))

def add_attempt(pid,q,ok,hint,seconds,mode="Practice"):
    c=cx(); xp=13 if ok and not hint else 10 if ok else 2; stars=1 if ok else 0
    sub=q.get("subskill",q.get("skill",""))
    c.execute("""INSERT INTO attempts(profile_id,question_id,subject,skill,subskill,grade,correct,used_hint,seconds,mode)
                 VALUES(?,?,?,?,?,?,?,?,?,?)""",(pid,q["id"],q["subject"],q["skill"],sub,q["grade"],int(ok),int(hint),seconds,mode))
    c.execute("UPDATE profiles SET xp=xp+?,stars=stars+?,answer_streak=CASE WHEN ?=1 THEN answer_streak+1 ELSE 0 END WHERE id=?",(xp,stars,int(ok),pid))
    _update_daily_streak(c,pid)
    r=c.execute("SELECT score FROM mastery WHERE profile_id=? AND subject=? AND skill=? AND subskill=?",(pid,q["subject"],q["skill"],sub)).fetchone()
    ns=(r["score"]*.75+(100 if ok else 0)*.25) if r else (100 if ok else 0)
    c.execute("""INSERT INTO mastery(profile_id,subject,skill,subskill,score,attempts) VALUES(?,?,?,?,?,1)
                 ON CONFLICT(profile_id,subject,skill,subskill) DO UPDATE SET score=?,attempts=attempts+1""",
              (pid,q["subject"],q["skill"],sub,ns,ns))
    schedule_review(c,pid,q["id"],ok)
    c.commit();c.close();return xp,stars

def schedule_review(c,pid,qid,ok):
    row=c.execute("SELECT interval_days,ease,repetitions FROM review_queue WHERE profile_id=? AND question_id=?",(pid,qid)).fetchone()
    today=datetime.date.today()
    if row:
        interval,ease,reps=row["interval_days"],row["ease"],row["repetitions"]
    else:
        interval,ease,reps=1,2.0,0
    if ok:
        reps+=1
        interval=1 if reps==1 else 3 if reps==2 else max(4,round(interval*ease))
        ease=min(2.6,ease+0.05)
    else:
        reps=0; interval=1; ease=max(1.3,ease-0.2)
    next_date=today+datetime.timedelta(days=interval)
    c.execute("""INSERT INTO review_queue(profile_id,question_id,next_review,interval_days,ease,repetitions,last_result)
                 VALUES(?,?,?,?,?,?,?)
                 ON CONFLICT(profile_id,question_id) DO UPDATE SET next_review=?,interval_days=?,ease=?,repetitions=?,last_result=?""",
              (pid,qid,next_date.isoformat(),interval,ease,reps,int(ok),next_date.isoformat(),interval,ease,reps,int(ok)))

def due_review_ids(pid,limit=50):
    c=cx();today=datetime.date.today().isoformat()
    r=[x["question_id"] for x in c.execute("""SELECT question_id FROM review_queue WHERE profile_id=? AND next_review<=? ORDER BY next_review LIMIT ?""",(pid,today,limit))]
    c.close();return r

def mastery(pid):
    c=cx();r=[dict(x) for x in c.execute("SELECT * FROM mastery WHERE profile_id=?",(pid,))];c.close();return r
def attempts(pid,limit=999):
    c=cx();r=[dict(x) for x in c.execute("SELECT * FROM attempts WHERE profile_id=? ORDER BY id DESC LIMIT ?",(pid,limit))];c.close();return r
def rewards():
    c=cx();r=[dict(x) for x in c.execute("SELECT * FROM rewards WHERE active=1 ORDER BY stars_cost")];c.close();return r
def add_reward(n,cost):
    c=cx();c.execute("INSERT INTO rewards(name,stars_cost) VALUES(?,?)",(n,cost));c.commit();c.close()
def redeem(pid,r):
    p=get_profile(pid)
    if p["stars"]<r["stars_cost"]: return False
    c=cx();c.execute("UPDATE profiles SET stars=stars-? WHERE id=?",(r["stars_cost"],pid));c.execute("INSERT INTO redemptions(profile_id,reward_name,stars_cost) VALUES(?,?,?)",(pid,r["name"],r["stars_cost"]));c.commit();c.close();return True
def redemptions():
    c=cx();r=[dict(x) for x in c.execute("""SELECT r.*,p.name FROM redemptions r JOIN profiles p ON p.id=r.profile_id ORDER BY r.id DESC""")];c.close();return r
def set_redemption_status(rid,status):
    c=cx();c.execute("UPDATE redemptions SET status=? WHERE id=?",(status,rid));c.commit();c.close()
def award_badge(pid,b):
    c=cx();c.execute("INSERT OR IGNORE INTO badges(profile_id,badge) VALUES(?,?)",(pid,b));c.commit();c.close()
def badges(pid):
    c=cx();r=[dict(x) for x in c.execute("SELECT * FROM badges WHERE profile_id=?",(pid,))];c.close();return r
def save_racer(pid,subject,grade,seconds,accuracy):
    c=cx();r=c.execute("SELECT * FROM racer_scores WHERE profile_id=? AND subject=? AND grade=?",(pid,subject,grade)).fetchone()
    improved=(not r) or (accuracy>=r["best_accuracy"] and seconds<r["best_seconds"])
    if improved:
        c.execute("""INSERT INTO racer_scores(profile_id,subject,grade,best_seconds,best_accuracy) VALUES(?,?,?,?,?)
                     ON CONFLICT(profile_id,subject,grade) DO UPDATE SET best_seconds=?,best_accuracy=?,updated_at=CURRENT_TIMESTAMP""",
                  (pid,subject,grade,seconds,accuracy,seconds,accuracy))
    c.commit();c.close();return improved
def racer_best(pid,subject,grade):
    c=cx();r=c.execute("SELECT * FROM racer_scores WHERE profile_id=? AND subject=? AND grade=?",(pid,subject,grade)).fetchone();c.close();return dict(r) if r else None
def complete_project(pid,project_id,notes=""):
    c=cx();before=c.execute("SELECT 1 FROM project_completions WHERE profile_id=? AND project_id=?",(pid,project_id)).fetchone()
    c.execute("INSERT OR IGNORE INTO project_completions(profile_id,project_id,notes) VALUES(?,?,?)",(pid,project_id,notes))
    if not before:c.execute("UPDATE profiles SET xp=xp+50,stars=stars+5 WHERE id=?",(pid,))
    c.commit();c.close();return not before
def completed_projects(pid):
    c=cx();r=[dict(x) for x in c.execute("SELECT * FROM project_completions WHERE profile_id=?",(pid,))];c.close();return r
def weekly_stats(pid,days=7):
    c=cx()
    r=c.execute("""SELECT COUNT(*) n,COALESCE(AVG(correct)*100,0) acc,COUNT(DISTINCT date(created_at)) learning_days,
                   COALESCE(AVG(seconds),0) avg_seconds
                   FROM attempts WHERE profile_id=? AND created_at>=datetime('now',?)""",(pid,f"-{days} days")).fetchone()
    prev=c.execute("""SELECT COUNT(*) n,COALESCE(AVG(correct)*100,0) acc
                      FROM attempts WHERE profile_id=? AND created_at>=datetime('now',?) AND created_at<datetime('now',?)""",
                   (pid,f"-{days*2} days",f"-{days} days")).fetchone()
    c.close();return {"current":dict(r),"previous":dict(prev)}
def family_feed(limit=30):
    c=cx();r=[dict(x) for x in c.execute("""SELECT a.created_at,p.name,p.avatar,a.subject,a.skill,a.correct FROM attempts a JOIN profiles p ON p.id=a.profile_id ORDER BY a.id DESC LIMIT ?""",(limit,))];c.close();return r
