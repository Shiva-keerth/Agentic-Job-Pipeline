import os
import sqlite3

def purge_stale_jobs():
    db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get count before
    cursor.execute("SELECT COUNT(*) FROM applications WHERE verdict IS NULL OR verdict = ''")
    stale_count = cursor.fetchone()[0]

    if stale_count == 0:
        print("No stale rows found. Database is clean.")
    else:
        print(f"Found {stale_count} stale rows (scraped but never evaluated). Purging...")
        
        cursor.execute("DELETE FROM applications WHERE verdict IS NULL OR verdict = ''")
        conn.commit()
        
        print(f"Successfully deleted {stale_count} stale rows.")
    
    conn.close()

if __name__ == "__main__":
    purge_stale_jobs()
