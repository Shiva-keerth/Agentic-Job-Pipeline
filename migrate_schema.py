import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'outcome_log.db')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN resume_used TEXT DEFAULT 'N/A'")
        conn.commit()
        print("✅ Successfully added 'resume_used' column to applications table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ Column 'resume_used' already exists.")
        else:
            print(f"❌ Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
