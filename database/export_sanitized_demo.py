import sqlite3
import os
import shutil

def export_sanitized():
    db_path = os.path.join(os.path.dirname(__file__), "outcome_log.db")
    # Export to the standalone dashboard project folder
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "LLMOps_Observability_Dashboard", "demo_telemetry.db")
    
    if not os.path.exists(db_path):
        print("Real database not found.")
        return
        
    print(f"Exporting anonymized data to {demo_path}...")
    
    # Connect to both DBs
    src_conn = sqlite3.connect(db_path)
    src_cursor = src_conn.cursor()
    
    # Recreate demo DB from scratch
    if os.path.exists(demo_path):
        os.remove(demo_path)
    dest_conn = sqlite3.connect(demo_path)
    dest_cursor = dest_conn.cursor()
    
    # Recreate table in demo DB
    dest_cursor.execute("""
    CREATE TABLE evaluator_telemetry (
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
    
    # Read all telemetry
    src_cursor.execute("SELECT company, role, timestamp, eval_type, model_used, is_fallback, prompt_tokens, completion_tokens, latency_ms, verdict, reason FROM evaluator_telemetry")
    rows = src_cursor.fetchall()
    
    # Anonymize
    company_map = {}
    def get_safe_company(real_company):
        if not real_company: return "Unknown Company"
        if real_company not in company_map:
            # e.g., Company A, Company B... Company AA
            idx = len(company_map)
            suffix = "" if idx < 26 else str(idx // 26)
            char = chr(65 + (idx % 26))
            company_map[real_company] = f"Company {char}{suffix}"
        return company_map[real_company]
        
    sanitized_rows = []
    for row in rows:
        company = get_safe_company(row[0])
        # We leave role and other fields intact to show realistic dashboard data
        sanitized_rows.append((company,) + row[1:])
        
    dest_cursor.executemany("""
        INSERT INTO evaluator_telemetry 
        (company, role, timestamp, eval_type, model_used, is_fallback, prompt_tokens, completion_tokens, latency_ms, verdict, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sanitized_rows)
    
    dest_conn.commit()
    dest_conn.close()
    src_conn.close()
    print(f"Exported {len(sanitized_rows)} anonymized records.")

if __name__ == "__main__":
    export_sanitized()
