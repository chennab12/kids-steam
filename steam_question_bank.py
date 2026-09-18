import json
from pathlib import Path
BASE=Path(__file__).parent
QUESTIONS=json.loads((BASE/"data/questions.json").read_text(encoding="utf-8"))
PROJECTS=json.loads((BASE/"data/projects.json").read_text(encoding="utf-8"))
def filter_questions(subject=None,grade=None,difficulty=None):
    q=QUESTIONS
    if subject:q=[x for x in q if x["subject"]==subject]
    if grade:q=[x for x in q if x["grade"]==grade]
    if difficulty:q=[x for x in q if x["difficulty"]==difficulty]
    return q
def skills_for(subject,grade=None):
    return sorted({x["skill"] for x in filter_questions(subject,grade)})
def questions_by_ids(ids):
    s=set(ids); return [q for q in QUESTIONS if q["id"] in s]
def projects_for(grade,subject=None):
    p=[x for x in PROJECTS if x["grade_min"]<=grade<=x["grade_max"]]
    if subject:p=[x for x in p if x["subject"]==subject]
    return p
