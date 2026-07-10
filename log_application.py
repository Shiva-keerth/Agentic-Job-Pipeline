import sqlite3
from datetime import datetime
import argparse
import sys
import os

def log_application(platform, company, role, job_url="N/A", outcome="pending", resume="N/A"):
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'outcome_log.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate unique placeholder if URL is N/A
    if job_url == "N/A":
        job_url = f"manual_entry_{datetime.now().timestamp()}"
    
    # Check if job already exists by URL (if a real URL is provided)
    if not job_url.startswith("manual_entry_"):
        cursor.execute("SELECT id FROM applications WHERE job_url = ?", (job_url,))
        result = cursor.fetchone()
        if result:
            job_id = result[0]
            cursor.execute("""
                UPDATE applications 
                SET date_applied = ?, outcome = ?, resume_used = ?
                WHERE id = ?
            """, (today, outcome, resume, job_id))
            conn.commit()
            print(f"[SUCCESS] Updated existing job (ID: {job_id}) as applied with resume: {resume}")
            conn.close()
            return

    # Otherwise insert a manual record
    try:
        cursor.execute("""
            INSERT INTO applications (
                date_found, platform, company, role, job_url, jd_text, match_score, verdict, date_applied, outcome, resume_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            today, platform, company, role, job_url, 
            "Manual Entry", 100.0, "Manual Application", today, outcome, resume
        ))
        conn.commit()
        print(f"[SUCCESS] Successfully logged new manual application: {company} - {role} ({platform}) | Resume: {resume}")
    except Exception as e:
        print(f"[ERROR] Failed to log application: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log a manual job application to the Jobline Pipeline database.")
    parser.add_argument("--platform", type=str, required=True, help="Platform applied on (e.g., LinkedIn, Direct)")
    parser.add_argument("--company", type=str, required=True, help="Company name")
    parser.add_argument("--role", type=str, required=True, help="Job role")
    parser.add_argument("--url", type=str, default="N/A", help="Optional: Job URL to update existing pipeline job")
    parser.add_argument("--resume", type=str, default="N/A", help="Optional: Name of the resume used")
    
    args = parser.parse_args()
    log_application(args.platform, args.company, args.role, args.url, "pending", args.resume)
