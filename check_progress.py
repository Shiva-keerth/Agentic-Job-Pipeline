import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM applications WHERE platform = 'Remotive'")
print(f"Remotive jobs: {cursor.fetchone()[0]}")
cursor.execute("SELECT company, role, match_score, verdict FROM applications WHERE match_score > 0 ORDER BY match_score DESC LIMIT 5")
print("--- Top 5 ---")
for row in cursor.fetchall():
    print(f"Company: {row[0]} | Role: {row[1]} | Score: {row[2]} | Verdict: {row[3]}")
conn.close()
