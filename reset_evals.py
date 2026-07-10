import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Reset evaluation for all scored jobs to re-run with strict prompt
cursor.execute("UPDATE applications SET match_score = 0, verdict = 'Pending' WHERE verdict IN ('Good Fit', 'Strong Match', 'DISQUALIFIED', 'BLACKLISTED')")
conn.commit()
print(f"Reset {cursor.rowcount} jobs for re-evaluation.")
conn.close()
