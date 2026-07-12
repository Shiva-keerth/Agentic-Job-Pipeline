import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), "outcome_log.db")
    print(f"Migrating database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the telemetry table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluator_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,
        role TEXT,
        timestamp TEXT,
        eval_type TEXT,
        model_used TEXT,
        is_fallback BOOLEAN,
        prompt_tokens INTEGER,
        completion_tokens INTEGER,
        latency_ms REAL,
        verdict TEXT,
        reason TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print("Migration complete. `evaluator_telemetry` table is ready.")

if __name__ == "__main__":
    migrate()
