# STEAM Mesh V2

LearnMesh-inspired Streamlit family learning app for Science, Technology, Engineering, Arts and Math.

## Main functionality
- 500 grade-tagged questions
- Grades 2–7
- Five STEAM subjects
- Core 1 / Core 2 / Core 3 difficulty
- Family profile picker
- SQLite persistence
- XP, stars, streaks and levels
- Per-subject / per-skill mastery
- Weak-area recommendation
- Practice mode
- Timed tests
- Review missed questions
- Hints and explanations
- Badges
- Parent PIN
- Session limits and break reminders
- Custom reward catalog and redemption

## First-run parent PIN
`2468`

Change it in Parent Center immediately.

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Streamlit Cloud persistence
SQLite is good for local use and a live instance but is not ideal as durable cloud storage across redeploys. For production, replace `db.py` with Supabase/Postgres while keeping the same function interface.

## Recommended V3
- Supabase family auth and durable cloud persistence
- Puzzle Racer / personal best mode
- standards tagging (NGSS / Common Core / CSTA)
- spaced repetition scheduler
- parent approval queue for rewards
- weekly progress report
- validated AI follow-up questions
- hands-on STEAM build missions
