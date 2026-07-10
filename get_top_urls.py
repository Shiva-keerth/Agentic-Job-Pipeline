import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT company, role, match_score, job_url 
    FROM applications 
    WHERE verdict IN ('Strong Match', 'Good Fit')
    ORDER BY match_score DESC 
    LIMIT 10
""")

rows = cursor.fetchall()

if not rows:
    print("No strong/good matches found in the database yet.")
else:
    print("\n--- TOP 10 BEST JOBS TO APPLY TO ---")
    for i, row in enumerate(rows, 1):
        print(f"\n{i}. {row[1]} @ {row[0]}")
        print(f"   Score: {row[2]}")
        print(f"   URL: {row[3]}")

conn.close()
