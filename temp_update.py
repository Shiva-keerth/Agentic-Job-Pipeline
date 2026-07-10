import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Mark the ones we actually did in past sessions as applied
cursor.execute("UPDATE applications SET verdict = 'Manual Application', outcome = 'Applied' WHERE company IN ('Headway Tek Inc', 'UST')")

# Mark the useless ones as disqualified so they stop showing up
cursor.execute("UPDATE applications SET verdict = 'DISQUALIFIED - User Rejected', outcome = 'Rejected' WHERE company IN ('MyRemoteTeam Inc', 'Sonata Software')")

conn.commit()
conn.close()
print("Database updated successfully.")
