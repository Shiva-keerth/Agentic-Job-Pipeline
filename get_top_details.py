import sqlite3
import os
import json

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

companies = ["Headway Tek Inc", "UST"]

for company in companies:
    cursor.execute("SELECT role, match_score, verdict, jd_text FROM applications WHERE company=? ORDER BY match_score DESC LIMIT 1", (company,))
    row = cursor.fetchone()
    if row:
        print(f"--- {company} - {row[0]} ---")
        print(f"Score: {row[1]} | Verdict: {row[2]}")
        print("\nJD Snippet:")
        print(row[3][:1500] + "...\n")
        print("="*80 + "\n")

conn.close()
