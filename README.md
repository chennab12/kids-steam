# STEAM Quest — Kids Agentic Quiz App

A Streamlit quiz app inspired by the strongest LearnMesh-style interaction patterns, adapted to STEAM.

## Worlds
- Science
- Technology
- Engineering
- Arts
- Math

## Features
- child explorer profile
- grade-band selector
- three difficulty levels
- 3/5/10-question missions
- optional timer
- hints
- explanations
- XP and stars
- streaks
- mastery per subject
- adaptive difficulty
- badges
- character progression
- parent session limit setting
- reward catalog
- parent mastery view

## Agent loop
Choose subject → ask → hint → grade → explain → reward → update mastery → adapt difficulty → recommend weak area → next mission

## Run
```powershell
cd steam_kids_quiz_agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Best V2 upgrades
1. SQLite/Supabase persistent profiles
2. Real parent PIN and enforced session limits
3. 500+ grade-tagged questions
4. NGSS / Common Core / CSTA tags
5. Spaced repetition for missed concepts
6. AI-generated follow-up questions with validation
7. hands-on project missions
8. weekly parent report
9. skill-tree prerequisites
10. worksheet upload and custom quizzes
