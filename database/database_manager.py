import sqlite3, os

def init_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect("database/outcome_log.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            date_found    TEXT,
            platform      TEXT,
            company       TEXT,
            role          TEXT,
            job_url       TEXT UNIQUE,
            jd_text       TEXT,
            match_score   REAL,
            verdict       TEXT,
            date_applied  TEXT,
            outcome       TEXT DEFAULT 'pending',
            resume_used   TEXT DEFAULT 'N/A'
        )
    """)
    conn.commit()
    conn.close()
    print("DB initialized.")

if __name__ == "__main__":
    init_db()
