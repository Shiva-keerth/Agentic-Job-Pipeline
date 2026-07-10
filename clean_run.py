import sqlite3
import os
from main import run_pipeline

db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
conn = sqlite3.connect(db_path)
conn.execute("DELETE FROM applications")
conn.commit()
conn.close()
print("DB wiped. Running clean pipeline...")
run_pipeline()
