import sys
import io

# Force UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import time
from apscheduler.schedulers.background import BackgroundScheduler
from scrapers.linkedin_scraper import scrape_linkedin, save_to_db, KEYWORDS
from scrapers.remotive_scraper import scrape_remotive
from scrapers.remotive_scraper import save_to_db as remotive_save
from core.vector_ranker import build_vector_store
from core.llm_evaluator import run_evaluation

def run_pipeline():
    print("\n[Pipeline] Starting scheduled run...")
    
    # Step 1 \u2014 Scrape
    all_jobs = []
    for kw in KEYWORDS:
        results = scrape_linkedin(kw, pages=1)
        all_jobs.extend(results)
        time.sleep(3)
    save_to_db(all_jobs)
    
    # Remotive
    print("\n[Pipeline] Scraping Remotive...")
    remotive_jobs = scrape_remotive()
    remotive_save(remotive_jobs)
    
    # Step 2 \u2014 Embed new JDs
    build_vector_store()
    
    # Step 3 \u2014 Score top 50
    run_evaluation(top_n=50)
    
    print("[Pipeline] Run complete. Open Streamlit to review results.")

if __name__ == "__main__":
    # Run once immediately on start
    run_pipeline()
    
    # Then every 6 hours
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, "interval", hours=6)
    scheduler.start()
    
    print("[Pipeline] Scheduler running. Press Ctrl+C to stop.")
    print("[Pipeline] Open a second terminal and run: streamlit run ui/daily_digest_app.py")
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("[Pipeline] Stopped.")
