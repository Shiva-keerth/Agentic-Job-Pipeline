import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT company, role, match_score, job_url FROM applications WHERE verdict NOT IN ('DISQUALIFIED', 'BLACKLISTED') ORDER BY match_score DESC LIMIT 1")
print(cursor.fetchone())
conn.close()
