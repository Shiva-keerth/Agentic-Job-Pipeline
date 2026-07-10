from core.llm_evaluator import pre_filter_experience, EXPERIENCE_KILLERS
import sqlite3
import os
import re

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT role, jd_text FROM applications WHERE company='Jade Global'")
res = cursor.fetchone()
if res:
    role, jd_text = res
    text_to_check = (jd_text + " " + role).lower()
    print("Checking static killers...")
    for k in EXPERIENCE_KILLERS:
        if k in text_to_check:
            print(f"Caught by static: {k}")
    
    print("Checking Regex 1...")
    if re.search(r'([3-9]|\d{2,})\+?\s*(years?|yrs?)', text_to_check):
        print(f"Caught by regex 1")
    
    print("Checking Regex 2...")
    match = re.search(r'(\d+)\s*-\s*([3-9]|\d{2,})\s*(years?|yrs?)', text_to_check)
    if match:
        print(f"Caught by regex 2")
        
    print("Checking Regex 3...")
    if re.search(r'minimum\s+([3-9]|\d{2,})\s*(years?|yrs?)', text_to_check):
        print(f"Caught by regex 3")
conn.close()
