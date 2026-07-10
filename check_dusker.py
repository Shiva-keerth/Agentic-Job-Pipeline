import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT jd_text FROM applications WHERE company='Dusker AI'")
print(cursor.fetchone()[0])
conn.close()
