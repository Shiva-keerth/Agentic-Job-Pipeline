import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get total counts
cursor.execute("SELECT count(*) FROM applications")
total = cursor.fetchone()[0]
cursor.execute("SELECT count(*) FROM applications WHERE verdict = 'Pending' OR verdict IS NULL")
pending = cursor.fetchone()[0]

print(f"Total jobs in DB: {total} | Pending evaluation: {pending}")
print(f"\n{'='*90}")
print(f"{'#':<3} {'Company':<25} {'Role':<35} {'Score':<7} {'Verdict'}")
print(f"{'='*90}")

cursor.execute("""
    SELECT company, role, match_score, verdict, platform 
    FROM applications 
    WHERE match_score > 0 
    AND (verdict NOT LIKE '%Manual%' AND verdict NOT LIKE 'Applied%')
    AND outcome = 'pending'
    ORDER BY match_score DESC 
    LIMIT 10
""")
rows = cursor.fetchall()
for i, row in enumerate(rows, 1):
    print(f"{i:<3} {row[0]:<25} {row[1]:<35} {row[2]:<7} {row[3]} [{row[4]}]")

if not rows:
    print("No scored jobs found that haven't been applied to. Pipeline needs to run evaluation first.")

conn.close()
