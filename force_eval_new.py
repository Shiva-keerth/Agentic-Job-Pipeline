import sqlite3
from core.llm_evaluator import evaluate_job
from datetime import datetime, timedelta
import time

def run():
    print("Fetching new un-evaluated jobs from database...")
    conn = sqlite3.connect('database/outcome_log.db')
    c = conn.cursor()
    # Get jobs scraped in the last 48 hours that haven't been evaluated
    yesterday = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    c.execute("SELECT id, company, role, job_url, jd_text FROM applications WHERE date_found >= ? AND verdict IS NULL", (yesterday,))
    new_jobs = c.fetchall()
    
    print(f"Found {len(new_jobs)} brand new un-evaluated jobs. Evaluating the first 15 to find the best...")
    
    results = []
    # Evaluate a batch of 15 to find good ones quickly
    for db_id, company, role, job_url, jd_text in new_jobs[:15]:
        print(f"Evaluating: {role} @ {company}")
        job_dict = {"db_id": db_id, "company": company, "role": role, "url": job_url}
        evaluation = evaluate_job(job_dict, jd_text)
        
        if evaluation:
            score = evaluation.get("match_score", 0)
            verdict = evaluation.get("verdict", "Unknown")
            
            # Save to DB so we don't lose the evaluation
            c.execute("UPDATE applications SET match_score = ?, verdict = ? WHERE id = ?", (score, verdict, db_id))
            conn.commit()
            
            # Keep track of good jobs
            if score >= 40 and verdict not in ['BLACKLISTED', 'DISQUALIFIED']:
                results.append((company, role, score, verdict, job_url))
        time.sleep(1) # Rate limit buffer
        
    print("\n" + "="*80)
    print("TOP NEW JOBS (Today & Yesterday, Unapplied)")
    print("="*80)
    
    if not results:
        print("Evaluated 15 jobs, but none were strong matches. Run again to evaluate the rest of the queue.")
        return
        
    # Sort by score descending and print top 10
    sorted_results = sorted(results, key=lambda x: x[2], reverse=True)[:10]
    for r in sorted_results:
        print(f"{r[0]:<25} | {r[1]:<35} | Score: {r[2]:<4} | {r[3]}")
        print(f"Apply: {r[4]}")
        print("-" * 80)

if __name__ == "__main__":
    run()
