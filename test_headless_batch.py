import sqlite3
from playwright.sync_api import sync_playwright

def get_job_urls(limit=3):
    conn = sqlite3.connect("database/outcome_log.db")
    cursor = conn.cursor()
    cursor.execute("SELECT job_url FROM applications WHERE job_url IS NOT NULL LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def test_headless_batch():
    urls = get_job_urls(3)
    # Adding the original Agentic Loop URL to make it 4
    urls.append("https://in.linkedin.com/jobs/view/generative-ai-engineer-at-the-agentic-loop-4436823364")
    
    with sync_playwright() as p:
        print("Launching headless browser (zero cookies/auth)...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for url in urls:
            print(f"\nNavigating to {url}")
            try:
                page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception as e:
                print(f"Navigation complete (or timed out waiting for idle): {e}")
                
            content = page.query_selector('.job-details-module__content')
            if content:
                print(f"-> SUCCESS! Block DOES exist. Text:")
                print(f"'{content.inner_text().strip()}'")
            else:
                print("-> ABSENT. Block hidden from logged-out users.")
                
        browser.close()

if __name__ == "__main__":
    test_headless_batch()
