import json
from pathlib import Path
QUESTIONS=json.loads((Path(__file__).parent/"data/questions.json").read_text(encoding="utf-8"))
def filter_questions(subject=None,grade=None,difficulty=None):
    q=QUESTIONS
    if subject:q=[x for x in q if x["subject"]==subject]
    if grade:q=[x for x in q if x["grade"]==grade]
    if difficulty:q=[x for x in q if x["difficulty"]==difficulty]
    return q
def skills_for(subject,grade=None):
    return sorted({x["skill"] for x in filter_questions(subject,grade)})
