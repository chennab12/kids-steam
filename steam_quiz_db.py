import sqlite3,hashlib
from pathlib import Path
DB=Path(__file__).parent/"data/steam_mesh.db"
def cx():
    c=sqlite3.connect(DB,check_same_thread=False); c.row_factory=sqlite3.Row; return c
def hp(pin): return hashlib.sha256(("steam-mesh:"+pin).encode()).hexdigest()
def init_db():
    c=cx(); c.executescript("""
    CREATE TABLE IF NOT EXISTS family(id INTEGER PRIMARY KEY,pin_hash TEXT);
    CREATE TABLE IF NOT EXISTS profiles(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,grade INTEGER,avatar TEXT,xp INTEGER DEFAULT 0,stars INTEGER DEFAULT 0,streak INTEGER DEFAULT 0,session_limit INTEGER DEFAULT 20,break_reminder INTEGER DEFAULT 15,night_mode INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,profile_id INTEGER,question_id TEXT,subject TEXT,skill TEXT,grade INTEGER,correct INTEGER,used_hint INTEGER,seconds REAL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS mastery(profile_id INTEGER,subject TEXT,skill TEXT,score REAL DEFAULT 0,attempts INTEGER DEFAULT 0,PRIMARY KEY(profile_id,subject,skill));
    CREATE TABLE IF NOT EXISTS rewards(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,stars_cost INTEGER,active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS badges(profile_id INTEGER,badge TEXT,earned_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(profile_id,badge));
    CREATE TABLE IF NOT EXISTS redemptions(id INTEGER PRIMARY KEY AUTOINCREMENT,profile_id INTEGER,reward_name TEXT,stars_cost INTEGER,status TEXT DEFAULT 'requested',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
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
    c=cx(); r=[dict(x) for x in c.execute("SELECT * FROM profiles ORDER BY id")]; c.close(); return r
def get_profile(pid):
    c=cx(); r=c.execute("SELECT * FROM profiles WHERE id=?",(pid,)).fetchone(); c.close(); return dict(r)
def add_profile(name,grade,avatar):
    c=cx(); c.execute("INSERT INTO profiles(name,grade,avatar) VALUES(?,?,?)",(name,grade,avatar)); c.commit(); c.close()
def save_controls(pid,limit,br,night):
    c=cx(); c.execute("UPDATE profiles SET session_limit=?,break_reminder=?,night_mode=? WHERE id=?",(limit,br,int(night),pid)); c.commit(); c.close()
def add_attempt(pid,q,ok,hint,seconds):
    c=cx(); xp=13 if ok and not hint else 10 if ok else 2; stars=1 if ok else 0
    c.execute("INSERT INTO attempts(profile_id,question_id,subject,skill,grade,correct,used_hint,seconds) VALUES(?,?,?,?,?,?,?,?)",(pid,q["id"],q["subject"],q["skill"],q["grade"],int(ok),int(hint),seconds))
    c.execute("UPDATE profiles SET xp=xp+?,stars=stars+? WHERE id=?",(xp,stars,pid))
    r=c.execute("SELECT score FROM mastery WHERE profile_id=? AND subject=? AND skill=?",(pid,q["subject"],q["skill"])).fetchone()
    ns=(r["score"]*.75+(100 if ok else 0)*.25) if r else (100 if ok else 0)
    c.execute("INSERT INTO mastery(profile_id,subject,skill,score,attempts) VALUES(?,?,?,?,1) ON CONFLICT(profile_id,subject,skill) DO UPDATE SET score=?,attempts=attempts+1",(pid,q["subject"],q["skill"],ns,ns))
    c.commit(); c.close(); return xp,stars
def set_streak(pid,v):
    c=cx(); c.execute("UPDATE profiles SET streak=? WHERE id=?",(v,pid)); c.commit(); c.close()
def mastery(pid):
    c=cx(); r=[dict(x) for x in c.execute("SELECT * FROM mastery WHERE profile_id=?",(pid,))]; c.close(); return r
def attempts(pid,limit=999):
    c=cx(); r=[dict(x) for x in c.execute("SELECT * FROM attempts WHERE profile_id=? ORDER BY id DESC LIMIT ?",(pid,limit))]; c.close(); return r
def wrong_ids(pid):
    return [x["question_id"] for x in attempts(pid,100) if not x["correct"]]
def rewards():
    c=cx(); r=[dict(x) for x in c.execute("SELECT * FROM rewards WHERE active=1 ORDER BY stars_cost")]; c.close(); return r
def add_reward(n,cost):
    c=cx(); c.execute("INSERT INTO rewards(name,stars_cost) VALUES(?,?)",(n,cost)); c.commit(); c.close()
def redeem(pid,r):
    p=get_profile(pid)
    if p["stars"]<r["stars_cost"]: return False
    c=cx()
    c.execute("UPDATE profiles SET stars=stars-? WHERE id=?",(r["stars_cost"],pid))
    c.execute("INSERT INTO redemptions(profile_id,reward_name,stars_cost,status) VALUES(?,?,?,'requested')",(pid,r["name"],r["stars_cost"]))
    c.commit(); c.close(); return True

def redemptions():
    c=cx(); r=[dict(x) for x in c.execute("""SELECT r.*,p.name FROM redemptions r JOIN profiles p ON p.id=r.profile_id ORDER BY r.id DESC""")]; c.close(); return r

def set_redemption_status(rid,status):
    c=cx(); c.execute("UPDATE redemptions SET status=? WHERE id=?",(status,rid)); c.commit(); c.close()

def family_feed(limit=25):
    c=cx()
    r=[dict(x) for x in c.execute("""SELECT a.created_at,p.name,p.avatar,a.subject,a.skill,a.correct
      FROM attempts a JOIN profiles p ON p.id=a.profile_id
      ORDER BY a.id DESC LIMIT ?""",(limit,))]
    c.close(); return r
def award_badge(pid,b):
    c=cx(); c.execute("INSERT OR IGNORE INTO badges(profile_id,badge) VALUES(?,?)",(pid,b)); c.commit(); c.close()
def badges(pid):
    c=cx(); r=[dict(x) for x in c.execute("SELECT * FROM badges WHERE profile_id=?",(pid,))]; c.close(); return r
