import os
import json
import sqlite3
import argparse
import datetime

def save_round_to_db(json_filepath: str):
    if not os.path.exists(json_filepath):
        print(f"Error: Could not find file {json_filepath}")
        return

    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return
    
    if not jobs:
        print("No jobs found in the JSON file.")
        return

    db_path = os.path.join(os.path.dirname(__file__), "database", "outcome_log.db")
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ensure connection is established
    # (Removed CREATE TABLE to respect existing schema)

    added = 0
    updated = 0
    
    timestamp = datetime.datetime.utcnow().isoformat()

    for job in jobs:
        # Generate a unique ID based on URL or composite
        import hashlib
        job_url = job.get('url', job.get('job_url', ''))
        company = job.get('company', '')
        role = job.get('title', job.get('role', ''))
        
        if not job_url:
            continue
            
        job_id = hashlib.md5(job_url.encode('utf-8')).hexdigest()
        
        score = job.get('score', 0)
        verdict = job.get('verdict', 'UNKNOWN')
        
        # We will use INSERT OR IGNORE, and if it exists we might update it
        try:
            cursor.execute("""
                INSERT INTO applications 
                (date_found, platform, company, role, job_url, jd_text, match_score, verdict, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, "LinkedIn", company, role, job_url, "Imported from JSON", score, verdict, 'pending'))
            added += 1
        except sqlite3.IntegrityError:
            # Job exists, update score and verdict
            cursor.execute("""
                UPDATE applications 
                SET match_score = ?, verdict = ?, outcome = 'pending'
                WHERE job_url = ?
            """, (score, verdict, job_url))
            updated += 1

    conn.commit()
    conn.close()
    
    print(f"Database import complete! Added {added} new jobs, updated {updated} existing jobs.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save round JSON results to SQLite database.")
    parser.add_argument("json_file", help="Path to the top10_roundX_results.json file")
    args = parser.parse_args()
    
    save_round_to_db(args.json_file)
