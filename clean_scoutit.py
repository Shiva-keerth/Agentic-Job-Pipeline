import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
conn.execute("DELETE FROM applications WHERE LOWER(company) = 'scoutit'")
conn.commit()
conn.close()
print("Scoutit entries removed.")
