# STEAM Mesh V3

High-ROI V3 upgrade of the Streamlit kids STEAM learning app.

## V3 additions
- true daily learning streaks
- richer badges including 7-Day Streak, Racer, Comeback Kid
- skill/subskill prerequisite map
- spaced repetition review queue
- Puzzle Racer against the child's own personal best
- weekly parent analytics with week-over-week comparison
- hands-on STEAM project missions
- existing 500 grade-tagged questions enriched with:
  - domain
  - subskill
  - prerequisite
  - standards family
  - estimated time

## Preserved V2 features
- child profiles
- Grades 2–7
- Science, Technology, Engineering, Arts, Math
- XP and stars
- mastery
- practice
- timed tests
- hints and explanations
- rewards + parent approval
- parent PIN
- session limits and break reminders
- family feed

## First-run parent PIN
`2468`

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Deploy
Push the project to GitHub and deploy `app.py` with Streamlit Community Cloud.

## Production persistence note
SQLite is intentionally retained so V3 works immediately. For durable cloud persistence across redeploys, replace `steam_quiz_db.py` with a Supabase/Postgres implementation that preserves the same function interface.
