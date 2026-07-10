import sqlite3
import os
import re
from core.llm_evaluator import EXPERIENCE_KILLERS

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT role, jd_text FROM applications WHERE company='BDO India'")
res = cursor.fetchone()
if res:
    role, jd_text = res
    text = (jd_text + " " + role).lower()
    print("Checking BDO India...")
    for k in EXPERIENCE_KILLERS:
        if re.search(rf'\b{re.escape(k)}\b', text):
            print(f"Caught by static: {k}")
    
    if re.search(r'([3-9]|\d{2,})\+?\s*(years?|yrs?)', text):
        print(f"Caught by regex 1")
    
    if re.search(r'(\d+)\s*-\s*([3-9]|\d{2,})\s*(years?|yrs?)', text):
        print(f"Caught by regex 2")
        
    if re.search(r'minimum\s+([3-9]|\d{2,})\s*(years?|yrs?)', text):
        print(f"Caught by regex 3")
conn.close()
